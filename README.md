# Coupa Framework

Framework desktop (PyQt6) com automações para o fluxo de compras no Coupa: extração de dados, download de orçamentos, geração de PDF de pedidos, organização de arquivos e disparo de e-mails.

## Setup local

1. `pip install -r requirements.txt`
2. `playwright install` (baixa os browsers usados pela automação)
3. Copie `.env.example` para `.env` e preencha com os valores reais da sua instância Coupa:
   - `COUPA_BASE_URL`
   - `COUPA_FW_SECRET`
4. `python main.py`

Os arquivos `coupa_profiles.json`, `coupa_profiles.salt`, mapeamentos de fornecedores/unidades e relatórios gerados não fazem parte do repositório (veja `.gitignore`) — são dados locais/sensíveis de cada instalação.
