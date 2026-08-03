# Coupa Framework

Framework desenvolvido em Python para automatizar processos na plataforma Coupa.

## Recursos

- **Aba 1 — Extrator Inteligente**: extrai dados de requisições (pedido, fornecedor, criado por, destino) via automação do Edge
- **Aba 2 — Baixador de Orçamentos**: baixa e filtra anexos de propostas/cotações das requisições
- **Aba 3 — Gerador de PDF de Pedidos**: gera PDFs dos pedidos de compra diretamente do portal Coupa
- **Aba 4 — Renomeador**: renomeia PDFs de pedidos com base nos dados extraídos (ID Coupa, fornecedor, unidade)
- **Aba 5 — Organizador**: organiza arquivos em pastas por fornecedor com base em uma planilha de controle
- **Aba 6 — Disparo de E-mails**: envia e-mails de autorização de compra via SMTP ou Outlook
- **Fluxo Automático (Modo Cadeia)**: executa as abas 2–6 em sequência após a extração da Aba 1

## Pré-requisitos

- Python 3.10 ou superior
- Microsoft Edge instalado (o framework usa o Edge para automação web via Playwright)
- Windows 10/11 (64-bit)

## Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/DuduProKill/Framework
cd "CoupaFramework v1.1"

# 2. Crie e ative um ambiente virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Instale o driver do Playwright para o Edge
playwright install msedge

# 5. Configure as variáveis de ambiente (veja seção abaixo)
copy .env.example .env
# Edite o .env com seus valores

# 6. Execute o framework
python main.py
```

## Configuração do `.env`

Crie um arquivo `.env` na raiz do projeto (nunca versione este arquivo):

```env
# URL da sua instância Coupa (obrigatório)
COUPA_BASE_URL=https://sua-instancia.coupahost.com

# Segredo para criptografia dos perfis (recomendado; se omitido, uma chave
# aleatória é gerada e persistida localmente em coupa_fw.secret)
COUPA_FW_SECRET=sua-chave-secreta-aqui

# Caminhos das planilhas de mapeamento para disparo de e-mails (opcional)
MAP_FORNECEDORES=C:\caminho\para\mapeamento_fornecedores.xlsx
MAP_UNIDADES=C:\caminho\para\mapeamento_unidades.xlsx

# Caminho do executável do Edge (opcional; detectado automaticamente se omitido)
EDGE_EXECUTABLE_PATH=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
```

## Logs

Os logs de execução são gravados automaticamente em:

```
%APPDATA%\CoupaFramework\logs\coupa_framework.log
```

Rotação automática: máximo de 2 MB por arquivo, 5 arquivos de backup.

## Build do instalador

```bat
build_installer.bat
```

Requer [Inno Setup 6](https://jrsoftware.org/isdl.php) instalado. O script detecta automaticamente o caminho do ISCC nas localizações padrão.

## Tecnologias

- Python 3.10+
- Selenium / Playwright (automação do Edge)
- PyQt6 (interface gráfica)
- PyMuPDF (extração de texto de PDFs)
- OpenPyXL / pandas (planilhas)
- python-docx (documentos Word)
- cryptography (criptografia de perfis)

## Objetivo

Reduzir tarefas repetitivas e aumentar a produtividade dos processos de compras e Supply Chain.
