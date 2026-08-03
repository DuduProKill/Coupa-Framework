import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
from PyQt6.QtCore import QThread, pyqtSignal

from modules.config import (
    MAX_TENTATIVAS,
    ESPERA_ENTRE_TENTATIVAS,
    TEXTOS_SEM_DOCUMENTO,
    MARGENS_IMPRESSAO,
    URL_TESTE_LOGIN,
    URL_BASE_IMPRESSAO_PDF,
    PERFIL_EDGE_PDF,
    resolve_edge_executable,
)
from modules.playwright_pool import PlaywrightContextSyncManager


class PdfGeneratorWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)

    def __init__(
        self,
        pedidos: List[str],
        pasta_saida: str,
        requisicoes_por_pedido: Dict[str, List[str]] = None,
    ):
        super().__init__()
        self.pedidos = pedidos
        self.pasta_saida = Path(pasta_saida)
        self.requisicoes_por_pedido = requisicoes_por_pedido or {}
        self.page = None
        self.cancelado = False

    def gerar_relatorio(self, resultados: Dict[str, Dict[str, str]]) -> Path:
        linhas = []
        for pedido in self.pedidos:
            resultado = resultados.get(pedido, {"status": "Cancelado", "detalhe": "Não processado"})
            requisicoes = self.requisicoes_por_pedido.get(pedido) or ["Não informada"]
            for requisicao in requisicoes:
                linhas.append(
                    {
                        "Número da Requisição": requisicao,
                        "Número do Pedido": pedido,
                        "Status": resultado["status"],
                        "Detalhe": resultado["detalhe"],
                        "Arquivo PDF": f"{pedido}.pdf" if resultado["status"] == "Sucesso" else "",
                    }
                )

        caminho = self.pasta_saida / f"Relatorio_Geracao_PDF_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
            pd.DataFrame(linhas).to_excel(writer, index=False, sheet_name="Resultado PDFs")
            planilha = writer.sheets["Resultado PDFs"]
            planilha.freeze_panes = "A2"
            for coluna in planilha.columns:
                letra = coluna[0].column_letter
                planilha.column_dimensions[letra].width = min(
                    max(len(str(c.value or "")) for c in coluna) + 2, 60
                )
        return caminho

    def run(self):
        self.log_signal.emit(">>> Inicializando o ambiente do Edge...")
        self.pasta_saida.mkdir(parents=True, exist_ok=True)

        sucesso, sem_documento, falha = [], [], []
        resultados = {}
        total = len(self.pedidos)

        try:
            caminho_edge = resolve_edge_executable()
            if not caminho_edge:
                self.log_signal.emit("ERRO CRÍTICO: Microsoft Edge não encontrado para geração de PDF.")
                self.finished_signal.emit("Microsoft Edge não encontrado para geração de PDF.")
                return

            # Melhoria 4: usa PlaywrightContextSyncManager padronizado do pool.
            # O 'with' gerencia o ciclo de vida completo (start/close/stop).
            with PlaywrightContextSyncManager(user_data_dir=str(PERFIL_EDGE_PDF)) as context:
                self.page = context.new_page()
                self.page.goto(URL_TESTE_LOGIN, wait_until="networkidle")

                if "login" in self.page.url.lower() or self.page.query_selector("input[type='password']"):
                    self.log_signal.emit("⚠️ Login necessário! Conclua o login corporativo na janela do Edge...")
                    self.page.wait_for_url(lambda u: "login" not in u.lower(), timeout=300000)
                    self.log_signal.emit("✅ Autenticado com sucesso no portal Coupa!")

                self.log_signal.emit(f">>> Processando lote de {total} pedido(s)...")

                for i, ped in enumerate(self.pedidos, 1):
                    if self.cancelado:
                        break

                    url_print = URL_BASE_IMPRESSAO_PDF.format(pedido=ped)
                    self.log_signal.emit(f"📄 Abrindo leiaute de impressão para o Pedido #{ped}...")

                    try:
                        self.page.goto(url_print, wait_until="networkidle", timeout=45000)

                        doc_pronto = False
                        for tentativa in range(1, MAX_TENTATIVAS + 1):
                            conteudo = self.page.content().lower()
                            existe_erro = any(texto_err.lower() in conteudo for texto_err in TEXTOS_SEM_DOCUMENTO)

                            if not existe_erro:
                                doc_pronto = True
                                break

                            if tentativa < MAX_TENTATIVAS:
                                self.log_signal.emit(
                                    f"⏳ Documento do Pedido #{ped} ainda em processamento. Tentando recarregar em {ESPERA_ENTRE_TENTATIVAS}s..."
                                )
                                QThread.msleep(int(ESPERA_ENTRE_TENTATIVAS * 1000))
                                self.page.reload(wait_until="networkidle")

                        if doc_pronto:
                            self.page.emulate_media(media="print")
                            destino_pdf = self.pasta_saida / f"{ped}.pdf"
                            self.page.pdf(
                                path=str(destino_pdf),
                                format="A4",
                                print_background=True,
                                margin=MARGENS_IMPRESSAO,
                            )
                            self.log_signal.emit(f"✅ Sucesso: Pedido {ped} compilado em {destino_pdf.name}")
                            sucesso.append(ped)
                            resultados[ped] = {
                                "status": "Sucesso",
                                "detalhe": "PDF gerado com sucesso",
                            }
                        else:
                            self.log_signal.emit(f"⚠️ Pulado: Pedido {ped} ainda está em processamento interno.")
                            sem_documento.append(ped)
                            resultados[ped] = {
                                "status": "Erro",
                                "detalhe": "Documento ainda em processamento interno",
                            }

                    except Exception as e:
                        self.log_signal.emit(f"❌ Falha no processamento do Pedido #{ped}: {str(e)}")
                        falha.append(ped)
                        resultados[ped] = {"status": "Erro", "detalhe": str(e)}

                    self.progress_signal.emit(int((i / total) * 100))

            relatorio = self.gerar_relatorio(resultados)
            self.log_signal.emit(f"📊 Relatório salvo em: {relatorio}")
            resumo = (
                f"Processo concluído: {len(sucesso)} Sucesso(s) | {len(sem_documento)} Sem Doc | "
                f"{len(falha)} Falha(s). Relatório: {relatorio.name}"
            )
            self.finished_signal.emit(resumo)

        except Exception as e:
            self.log_signal.emit(f"❌ ERRO CRÍTICO na Thread do Gerador: {str(e)}")
            for pedido in self.pedidos:
                resultados.setdefault(pedido, {"status": "Erro", "detalhe": f"Falha interna: {str(e)}"})
            try:
                relatorio = self.gerar_relatorio(resultados)
                self.log_signal.emit(f"📊 Relatório salvo em: {relatorio}")
                self.finished_signal.emit(
                    f"Ocorreu uma falha interna na execução do Edge. Relatório: {relatorio.name}"
                )
            except Exception as erro_relatorio:
                self.log_signal.emit(f"❌ Não foi possível gerar o relatório: {erro_relatorio}")
                self.finished_signal.emit(
                    "Ocorreu uma falha interna na execução do Edge."
                )

    def cancelar(self):
        self.cancelado = True
