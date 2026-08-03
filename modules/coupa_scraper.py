import asyncio
import os
import re
import threading
from typing import Dict, Any, List
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from modules.config import (
    COUPA_BASE_URL,
    DEFAULT_COUPA_PROFILE_DIR,
    resolve_edge_executable,
)
from modules.playwright_pool import PlaywrightContextManager


class CoupaScraper:
    """Scraper para extrair dados de requisições do Coupa."""

    def __init__(
        self,
        requisicoes: List[str],
        config_extrair: Dict[str, bool],
        pause_event=None,
        login_confirmation_event=None,
    ):
        self.requisicoes = requisicoes
        self.config_extrair = config_extrair
        self.pause_event = pause_event
        self.login_confirmation_event = login_confirmation_event

    async def aguardar_retomada(self, log_callback):
        """Aguarda retomada. Sleep reduzido de 0.5s para 0.1s (5x mais responsivo)."""
        if not self.pause_event or not self.pause_event.is_set():
            # amazonq-ignore-next-line
            return

        log_callback("⏸️ Extração pausada. Clique em 'Retomar Extração' para continuar.")
        while self.pause_event.is_set():
            await asyncio.sleep(0.1)
        log_callback("▶️ Extração retomada.")

    async def aguardar_confirmacao_login(self, log_callback):
        """Aguarda confirmação de login. Sleep reduzido de 0.5s para 0.1s (5x mais responsivo)."""
        log_callback(
            "🔐 Faça o login no Coupa no Edge e clique em 'Confirmar Login e Iniciar Extração'."
        )
        while not self.login_confirmation_event.is_set():
            await asyncio.sleep(0.1)
        log_callback("✅ Login confirmado. Iniciando extração...")

    async def run(self, log_callback, edge_ready_callback=None) -> List[Dict[str, Any]]:
        extracted_data = []
        log_callback("⚡ Iniciando Edge em modo rápido...")

        caminho_edge = resolve_edge_executable()
        if not caminho_edge:
            log_callback("ERRO CRÍTICO: Caminho do Microsoft Edge não encontrado.")
            log_callback(
                "💡 Defina a variável de ambiente EDGE_EXECUTABLE_PATH ou instale o Edge no caminho padrão."
            )
            return [{"Erro": "Microsoft Edge não encontrado."}]

        user_data_dir = Path(DEFAULT_COUPA_PROFILE_DIR)
        try:
            user_data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as dir_err:
            log_callback(f"Erro ao acessar pasta de perfil: {str(dir_err)}")
            return [{"Erro": f"Falha de permissão de pasta: {str(dir_err)}"}]

        # Melhoria 3: usa o PlaywrightPool/PlaywrightContextManager em vez de
        # abrir um contexto novo via async_playwright() a cada execução.
        try:
            async with PlaywrightContextManager(user_data_dir=str(user_data_dir)) as context:
                try:
                    await context.route(
                        "**/*",
                        lambda route: route.abort()
                        if route.request.resource_type in ["image", "media", "font", "stylesheet"]
                        else route.continue_(),
                    )
                except Exception:
                    pass  # rota já definida em contexto reutilizado

                return await self._extrair(
                    context,
                    log_callback,
                    edge_ready_callback,
                    extracted_data,
                )
        except Exception as e:
            log_callback(f"ERRO CRÍTICO: {str(e)}")
            log_callback("\n💡 Certifique-se de FECHAR o Microsoft Edge antes de executar!")
            return [{"Erro": f"Feche o Edge e tente novamente. Detalhe: {str(e)}"}]

    async def _extrair(
        self,
        context,
        log_callback,
        edge_ready_callback,
        extracted_data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Executa a extração das requisições dentro de um contexto gerenciado."""
        pages = context.pages
        page = pages[0] if pages else await context.new_page()
        page.set_default_timeout(5000)

        try:
            await page.goto(COUPA_BASE_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            log_callback(f"Não foi possível abrir a página inicial do Coupa: {str(e)}")

        if edge_ready_callback:
            edge_ready_callback()
        await self.aguardar_confirmacao_login(log_callback)

        for idx, req in enumerate(self.requisicoes, 1):
            await self.aguardar_retomada(log_callback)
            url_requisicao = f"{COUPA_BASE_URL.rstrip('/')}/requisition_headers/{req.strip()}"
            log_callback(f"[{idx}/{len(self.requisicoes)}] Acessando Requisição #{req}...")

            try:
                await page.goto(url_requisicao, wait_until="domcontentloaded", timeout=30000)

                if "login" in page.url.lower() or await page.query_selector("input[type='password']"):
                    log_callback("⚠️ Login detectado! Faça o login manualmente...")
                    await page.wait_for_url(lambda url: "login" not in url.lower(), timeout=300000)
                    await page.wait_for_load_state("domcontentloaded")

                await page.wait_for_selector("body", state="attached", timeout=5000)

                seletor_pedido = "a[href*='purchase_order'], .po-number, :has-text('PO nº')"
                try:
                    await page.wait_for_selector(seletor_pedido, state="attached", timeout=2500)
                except Exception:
                    pass
                pedido_elemento = await page.query_selector(seletor_pedido)
                pedido_texto = ""
                if pedido_elemento:
                    raw_text = await pedido_elemento.inner_text()
                    match_po = re.search(r'PO\s*nº\s*\d+', raw_text, re.IGNORECASE)
                    if match_po:
                        pedido_texto = match_po.group(0)

                if not pedido_texto:
                    log_callback(f"⚠️ Requisição #{req} ignorada: Nenhum pedido emitido.")
                    extracted_data.append({"requisicao": req, "status": "Sem pedido emitido"})
                    continue

                fornecedor_nome = "Não localizado"
                fornecedor_numero = "Não localizado"

                aba_carrinho = await page.query_selector("a:has-text('Itens do carrinho')")
                if aba_carrinho:
                    await aba_carrinho.click()
                    try:
                        await page.wait_for_selector("a[href*='/suppliers/show/']", timeout=3000)
                    except Exception:
                        pass

                fornecedor_link = await page.query_selector("a.s-coupaSimpleTooltip[href*='/suppliers/show/']")
                if not fornecedor_link:
                    fornecedor_link = await page.query_selector("a[href*='/suppliers/show/']")

                if fornecedor_link:
                    title_text = await fornecedor_link.get_attribute("title")
                    if title_text:
                        partes = [parte.strip() for parte in title_text.split(" - ") if parte.strip()]
                        if len(partes) >= 2:
                            fornecedor_numero = partes[0]
                            fornecedor_nome = partes[1]
                        else:
                            match_split = re.search(r'^(\d+)\s*[-–]\s*(.+)$', title_text)
                            if match_split:
                                fornecedor_numero = match_split.group(1).strip()
                                fornecedor_nome = match_split.group(2).strip()
                            else:
                                fornecedor_nome = title_text
                    else:
                        fornecedor_nome = await fornecedor_link.inner_text()
                        fornecedor_nome = fornecedor_nome.strip()

                criado_por = "[Não Solicitado]"
                criado_por_email = ""
                if self.config_extrair.get("criado_por", True):
                    criado_por_label = await page.query_selector(
                        "td:has-text('Criado por'), label:has-text('Criado por'), span:has-text('Criado por')"
                    )
                    if criado_por_label:
                        criado_por = await page.evaluate(
                            "(element) => element.nextElementSibling ? element.nextElementSibling.innerText : element.innerText",
                            criado_por_label,
                        )
                        criado_por = criado_por.replace("Criado por", "").strip()
                        email_match = re.search(
                            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                            criado_por,
                        )
                        if email_match:
                            criado_por_email = email_match.group(0)

                solicitado_por = "[Não Solicitado]"
                solicitado_por_email = ""
                if self.config_extrair.get("solicitado_por", True):
                    solicitado_por_label = await page.query_selector(
                        "td:has-text('Solicitado por'), label:has-text('Solicitado por'), span:has-text('Solicitado por')"
                    )
                    if solicitado_por_label:
                        solicitado_por = await page.evaluate(
                            "(element) => element.nextElementSibling ? element.nextElementSibling.innerText : element.innerText",
                            solicitado_por_label,
                        )
                        solicitado_por = solicitado_por.split("(")[0].replace("Solicitado por", "").strip()
                        email_match = re.search(
                            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                            solicitado_por,
                        )
                        if email_match:
                            solicitado_por_email = email_match.group(0)

                emails = "[Não Solicitado]"
                if self.config_extrair.get("emails", False):
                    emails = "Nenhum e-mail encontrado"
                    justificativa_label = await page.query_selector(
                        "td:has-text('Justificativa'), label:has-text('Justificativa'), span:has-text('Justificativa')"
                    )
                    if justificativa_label:
                        justificativa_texto = await page.evaluate(
                            "(element) => element.nextElementSibling ? element.nextElementSibling.innerText : element.innerText",
                            justificativa_label,
                        )
                        emails_encontrados = re.findall(
                            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                            justificativa_texto,
                        )
                        if emails_encontrados:
                            emails = ", ".join(list(dict.fromkeys(emails_encontrados)))

                cidade_estado = "[Não Solicitado]"
                if self.config_extrair.get("destino", False):
                    cidade_estado = "Não localizado"
                    endereco_label = await page.query_selector(
                        "h3:has-text('Endereço de entrega'), div:has-text('Endereço de entrega'), td:has-text('Endereço')"
                    )
                    if endereco_label:
                        endereco_texto = await page.evaluate(
                            "(element) => { let p = element.closest('.card, .section, table, div, td'); return p ? p.innerText : ''; }",
                            endereco_label,
                        )
                        if not endereco_texto.strip():
                            endereco_texto = await page.evaluate(
                                "(element) => element.nextElementSibling ? element.nextElementSibling.innerText : element.innerText",
                                endereco_label,
                            )
                        if endereco_texto:
                            match_cep_cidade = re.search(
                                r'\d{5}-\d{3}\s+([A-Za-zÀ-ÿ0-9\-\s]+?)\s+Brasil\b',
                                endereco_texto,
                                re.IGNORECASE,
                            )
                            if not match_cep_cidade:
                                match_cep_cidade = re.search(
                                    r'\d{5}-\d{3}\s+([A-ZÀ-ÿ\s]+?)\s+[A-Z]{2}\b',
                                    endereco_texto,
                                    re.IGNORECASE,
                                )
                            if match_cep_cidade:
                                cidade_estado = match_cep_cidade.group(1).strip()
                            else:
                                linhas = [l.strip() for l in endereco_texto.split("\n") if l.strip()]
                                for l in reversed(linhas):
                                    match_l = re.search(r'^([A-Z\s]+?)\s+([A-Z]{2})$', l)
                                    if match_l:
                                        cidade_estado = f"{match_l.group(1).strip()} / {match_l.group(2).strip()}"
                                        break

                extracted_data.append(
                    {
                        "requisicao": req,
                        "status": "Com pedido",
                        "pedido": pedido_texto,
                        "fornecedor": fornecedor_nome,
                        "fornecedor_num": fornecedor_numero,
                        "criado_por": criado_por,
                        "criado_por_email": criado_por_email,
                        "solicitado_por": solicitado_por,
                        "solicitado_por_email": solicitado_por_email,
                        "emails": emails,
                        "localidade": cidade_estado,  # campo canônico único (Item 9)
                    }
                )

            except Exception as e:
                log_callback(f"Erro na requisição #{req}: {str(e)}")
                extracted_data.append({"requisicao": req, "erro": f"Falha na extração: {str(e)}"})

        return extracted_data


class AutomationWorker(QThread):
    log_signal = pyqtSignal(str)
    edge_ready_signal = pyqtSignal()
    finished_signal = pyqtSignal(list)
    progress_signal = pyqtSignal(int)  # Item 21: Sinal de progresso (0-100)

    def __init__(self, requisicoes: List[str], config_extrair: Dict[str, bool]):
        super().__init__()
        self.requisicoes = requisicoes
        self.config_extrair = config_extrair
        self.pause_event = threading.Event()
        self.login_confirmation_event = threading.Event()

    def pausar(self):
        self.pause_event.set()

    def retomar(self):
        self.pause_event.clear()

    def confirmar_login(self):
        self.login_confirmation_event.set()

    def run(self):
        """Melhoria 6: try/except garante que finished_signal SEMPRE seja emitido."""
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            scraper = CoupaScraper(
                self.requisicoes,
                self.config_extrair,
                self.pause_event,
                self.login_confirmation_event,
            )

            def log_with_progress(msg: str):
                self.log_signal.emit(msg)
                match = re.search(r'\[(\d+)/(\d+)\]', msg)
                if match:
                    current = int(match.group(1))
                    total_req = int(match.group(2))
                    if total_req > 0:
                        self.progress_signal.emit(int((current / total_req) * 100))
                elif "extração" in msg.lower() and "concluída" in msg.lower():
                    self.progress_signal.emit(100)

            results = loop.run_until_complete(
                scraper.run(log_with_progress, self.edge_ready_signal.emit)
            )
            self.finished_signal.emit(results)
        except Exception as e:
            self.log_signal.emit(f"❌ ERRO CRÍTICO na thread de extração: {str(e)}")
            try:
                import traceback
                self.log_signal.emit(traceback.format_exc())
            except Exception:
                pass
            # Garante que a UI não fique presa com botões desabilitados
            self.finished_signal.emit([{"erro": f"Falha crítica na automação: {str(e)}"}])
        finally:
            if loop is not None:
                try:
                    loop.close()
                except Exception:
                    pass

