# Coupa Framework

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52)](https://www.riverbankcomputing.com/software/pyqt/)
[![CI](https://github.com/DuduProKill/Framework/actions/workflows/ci.yml/badge.svg)](https://github.com/DuduProKill/Framework/actions/workflows/ci.yml)

Coupa Framework é uma aplicação desktop em Python para automatizar fluxos operacionais relacionados a compras e supply chain na plataforma Coupa.

## Visão geral

O projeto reúne em uma interface única as etapas de:
- extração de dados de requisições;
- download e filtragem de anexos;
- geração de PDFs de pedidos;
- renomeação de arquivos;
- organização de documentos;
- envio de e-mails de autorização.

## Requisitos

- Python 3.10+
- Microsoft Edge instalado
- Windows 10/11 (64-bit)

## Instalação

```bash
git clone https://github.com/DuduProKill/Framework
cd "CoupaFramework v1.1"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install msedge
copy .env.example .env
```

Edite o arquivo .env com os valores da sua instância Coupa e execute:

```bash
python main.py
```

## Configuração

O projeto lê configurações via variáveis de ambiente ou arquivo .env. As principais opções incluem:
- COUPA_BASE_URL
- COUPA_FW_SECRET
- MAP_FORNECEDORES
- MAP_UNIDADES
- EDGE_EXECUTABLE_PATH

## Estrutura do projeto

- main.py: ponto de entrada da aplicação
- modules/: widgets, serviços e utilidades
- tests/: testes automatizados
- .github/workflows/: CI do repositório

## Qualidade

O repositório inclui:
- testes automatizados;
- checagem estática com Ruff;
- workflow de CI para pull requests e pushes principais.

## Status do projeto

- Estado atual: estável para uso operacional básico.
- Cobertura de testes: foco em fluxos principais de extração, renomeação e atualização.
- Manutenção: evolução contínua em arquitetura, confiabilidade e experiência do usuário.

## Licença

Este projeto é mantido como ferramenta interna/operacional e pode ser adaptado conforme necessidade.
