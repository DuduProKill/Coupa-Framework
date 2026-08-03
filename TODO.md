# TODO - Pontos de Melhoria (Revisão de Código)

Itens levantados na revisão de código completa do projeto. Ordenados por prioridade.

## 🐛 Críticos (podem quebrar o app)

- [x] **1. Dependência inexistente em `download_scraper.py` (quebra tudo)** ✅
  - `download_scraper.py` importa `from pptx import Presentation` e `from pypdf import PdfReader` no topo.
  - `requirements.txt` não inclui `python-pptx` nem `pypdf` (removidos no Item 18 do PROGRESSO.md).
  - Como `modules/__init__.py` importa `download_scraper`, qualquer `import modules` falha → app não sobe.
  - **FEITO:** adicionados `python-pptx>=0.6.21` e `pypdf>=3.0.0` ao `requirements.txt`.

- [x] **2. `playwright.driver` excluído no build → executável sem navegador** ✅
  - `coupa_framework.spec` tem `excludes=['playwright.driver']` e o `build_installer.bat` apaga `driver/package/lib` e `.local-browsers`.
  - O Playwright precisa do driver mesmo com `channel="msedge"`. Sem ele, o app empacotado pode falhar ao abrir o Edge.
  - **FEITO:** removido `playwright.driver` dos excludes do `.spec`; o `build_installer.bat` agora mantém a pasta `lib` do driver e só remove os browsers baixados (`.local-browsers`), mantendo o Edge instalado.

- [x] **3. `PlaywrightPool` existe mas nunca é usado (código morto)** ✅
  - Criado para reusar contextos (economia ~200-400MB RAM/aba), mas nenhum scraper o usa.
  - **FEITO:** `coupa_scraper.py` e `download_scraper.py` agora usam `PlaywrightContextManager` (do pool) em vez de `async_playwright()`. O `pdf_generator.py` (sync) segue isolado por usar `sync_playwright`.

## 🔴 Alta prioridade

- [x] **4. API Playwright inconsistente (async vs sync)** ✅
  - Scrapers usam `async_api`, `pdf_generator` usa `sync_api`. Padronizar (idealmente todos via `PlaywrightPool`) reduz RAM e complexidade.
  - **FEITO:** adicionado `PlaywrightContextSyncManager` ao `playwright_pool.py` (suporte a API síncrona). O `pdf_generator.py` foi migrado para usá-lo, centralizando a resolução do executável do Edge e a criação do contexto. Removido o hack frágil `self.context._impl_obj._playwright`.

- [x] **5. `ModoAutomatico` duplicado como pseudo-singleton em 3 widgets** ✅
  - `ui_downloader.py`, `ui_pdf_generator.py` e `ui_email_sender.py` declaram cada um a própria `_modo_automatico_instance`.
  - Não é singleton global real. Consolidar em um único ponto (o `fluxo_orquestrador.py` já centraliza o fluxo).
  - **FEITO:** `ModoAutomatico` já era singleton real via `__new__`. Removidos os atributos `self._modo_automatico` duplicados dos 3 widgets e centralizado o acesso em `get_modo_automatico()` no `fluxo_orquestrador.py`. O `AutomaticFlowRunner` também usa o mesmo ponto de acesso.

- [x] **6. Workers sem `try/except` no `run()`** ✅
  - `AutomationWorker.run()` e `DownloadWorker.run()` não protegem contra exceções.
  - Se algo lançar, a thread morre SEM emitir `finished_signal` → UI fica presa com botões desabilitados.
  - **FEITO:** `AutomationWorker.run()` e `DownloadWorker.run()` agora têm `try/except/finally` que garantem a emissão do `finished_signal` mesmo em caso de erro, e fecham o loop assíncrono de forma segura.

- [x] **7. Fallback de segredo hardcoded em `config.py`** ✅
  - `_derive_key` usa `secret = os.environ.get("COUPA_FW_SECRET", "troque-este-valor-no-ambiente")`.
  - Sem a variável, todos usam a mesma chave previsível conhecida → criptografia dos perfis fica fraca.
  - **FEITO:** adicionado `_get_secret()` que usa `COUPA_FW_SECRET` se definida, ou gera/persiste uma chave aleatória por máquina em `coupa_fw.secret` (evitando chave previsível conhecida).

- [x] **8. Logging inconsistente** ✅
  - `download_scraper.py` usa `print()` para erros em vez do `UILogger`.
  - Erros não aparecem na UI, só no console (e `console=False` no build).
  - **FEITO:** `download_scraper.py` agora usa `_log_callback` (via `log_signal`) para reportar erros na UI, com fallback para `logging` caso não haja callback. Removidos os `print()`.

## 🟡 Média

- [x] **9. Acoplamento residual `parent_fw` em `ui_coupa.py`** ✅
  - `validar_requisitos_fluxo` acessa `self.parent_fw.tab_downloader` etc. diretamente, duplicando a lógica que o `fluxo_orquestrador.py` já faz via `_get_widget`.
  - **FEITO:** validação já delegada ao `AutomaticFlowRunner.validar_pre_requisitos_abas`. Acoplamento residual eliminado.

- [x] **10. Type hints pendentes (Item 19 do PROGRESSO.md)** ✅
  - `download_scraper.py`, `ui_downloader.py`, `ui_organizador.py`, `config.py` têm métodos sem type hints.
  - **FEITO:** adicionados type hints nos métodos sem anotação em todos os arquivos listados.

- [x] **11. Testes mínimos (Item 20 pendente)** ✅
  - Só existem 2 testes. Não há testes para `DataBus`, `export_service`, `ProfileManager`, `Organizador`, `fluxo_orquestrador`.
  - **FEITO:** criados `test_data_bus.py`, `test_export_service.py`, `test_profile_manager.py`, `test_organizador.py`, `test_fluxo_orquestrador.py`.

- [x] **12. `_find_email_in_df` usa `df.iterrows()` (lento)** ✅
  - Percurso linha a linha em Python puro no `email_sender.py`. Para planilhas grandes, vetorizar com pandas.
  - **FEITO:** substituído `iterrows()` por operações vetorizadas com `str.contains` e `apply` do pandas.

- [x] **13. `buscar_arquivo_por_codigo` usa `rglob('*')` por linha** ✅
  - No `organizador.py`, percorre a árvore toda a cada linha da planilha (O(n×m)). Indexar a lista de arquivos uma única vez.
  - **FEITO:** `executar()` indexa os arquivos das pastas uma única vez antes do loop; `buscar_arquivo_por_codigo` recebe a lista pré-indexada.

- [x] **14. Caminhos hardcoded nos scripts de build** ✅
  - `build_installer.bat` fixa `C:\Users\eduardo.rafael\...\ISCC.exe`; `installer.iss` fixa caminhos do Edge.
  - **FEITO:** `build_installer.bat` busca o ISCC dinamicamente via `%LOCALAPPDATA%`, `%ProgramFiles%` e `%ProgramFiles(x86)%`; `installer.iss` usa `{pf}` e `{pf32}` do Inno Setup.

## 🟢 Baixa

- [x] **15. `MAX_TENTATIVAS = 1` anula o retry de PDF** ✅
  - O loop de recarga do `pdf_generator.py` nunca tenta de novo, já que `MAX_TENTATIVAS=1`.
  - **FEITO:** `MAX_TENTATIVAS` alterado para `3` em `config.py`.

- [x] **16. `import os` redundante dentro de `DownloadScraper.run()`** ✅
  - Reimportado no corpo do método sem necessidade.
  - **FEITO:** removido o `import os` de dentro do método `run()` (o `os` já é importado no topo do módulo).

- [x] **17. `ui_coupa.py` conecta `log_signal` direto ao `txt_logs.append`** ✅
  - Ignora o `UILogger`, então os logs da Aba 1 não têm as cores/prefixos das demais abas.
  - **FEITO:** `log_signal` agora conectado ao método `self.log` que usa `UILogger.auto`.

## 🔴 Alta prioridade (2ª revisão)

- [x] **18. Pool Playwright não totalmente aproveitado** ✅
  - `cleanup_all()` nunca era chamado → risco de vazamento de contexto/memória em sessões longas.
  - **FEITO:** adicionada função `cleanup_playwright_pool()` em `playwright_pool.py` (wrapper síncrono de `cleanup_all()`). `main.py` chama no `closeEvent` do `FrameworkApp`.

- [x] **19. Logging apenas na UI** ✅
  - `UILogger` só escrevia no `QTextEdit`. Se o app travasse, nenhum rastro ficava em disco.
  - **FEITO:** adicionado `RotatingFileHandler` em `logger.py` que espelha todos os logs em `%APPDATA%\CoupaFramework\logs\coupa_framework.log` (2 MB por arquivo, 5 backups).

- [x] **20. Duplicação `localidade`/`destino`** ✅
  - `coupa_scraper.py` gravava os dois campos com o mesmo valor; `export_service.py` e `ui_coupa.py` tratavam ambos.
  - **FEITO:** removido campo `destino` de `coupa_scraper.py`; `ui_coupa.py` e `export_service.py` usam apenas `localidade` como campo canônico.

## 🟡 Média (2ª revisão)

- [x] **21. Thread-safety de `DataBus` e `SpreadsheetCache`** ✅
  - Singletons sem `threading.Lock`; acessados de QThreads com risco de corrida.
  - **FEITO:** adicionado `threading.Lock` em `DataBus` (todos os métodos) e em `SpreadsheetCache` (`get`, `set`, `invalidate`, `clear`).

- [x] **22. Timer do `_on_progress` em `ui_coupa.py`** ✅
  - Ao atingir 100%, a barra era ocultada após 1.5s via `QTimer.singleShot`; se uma nova extração iniciasse antes, a barra sumia indevidamente.
  - **FEITO:** timer guardado em `self._progress_hide_timer`; ao iniciar nova extração, o timer anterior é cancelado com `.stop()` antes de criar um novo.

- [x] **23. Configs hardcoded em `download_scraper.py` e `ui_renomeador.py`** ✅
  - `.coupa_edge_profile` fixo na home do usuário; `historico_renomeador.csv` gravado na raiz do projeto.
  - **FEITO:** adicionados `PERFIL_EDGE_DOWNLOAD` e `HISTORICO_RENOMEADOR` em `config.py` apontando para `%LOCALAPPDATA%\CoupaFramework\...` e `%APPDATA%\CoupaFramework\...`. Ambos os arquivos importam e usam as constantes centralizadas.

## 🟢 Baixa (2ª revisão)

- [x] **24. Dependências sem pinning** ✅
  - `requirements.txt` usava `>=` sem lock, impedindo builds reproduzíveis.
  - **FEITO:** versões pinadas com `==` baseadas no `pip freeze` do ambiente de desenvolvimento (julho 2025).

- [x] **25. README minimalista** ✅
  - Faltavam instruções de instalação, configuração do `.env`, requisito do Edge e descrição das abas.
  - **FEITO:** README reescrito com pré-requisitos, passos de instalação, tabela de variáveis do `.env`, informação sobre logs e instrução de build.
