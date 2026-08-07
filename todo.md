# TODO - Melhorias futuras

## UX e experiência
- [x] Melhorar a tela de módulos bloqueados com um layout mais profissional e instruções mais claras.
- [x] Adicionar um botão de "Reinstalar módulo" ou "Ativar módulo" após a instalação.
- [x] Exibir uma mensagem de sucesso ao finalizar a instalação de um módulo.
- [x] Permitir selecionar vários módulos de uma vez no instalador com botões "Selecionar tudo" e "Desmarcar tudo".
- [x] Mostrar um resumo final na instalação com os módulos escolhidos.

## Instalação e distribuição
- [ ] Criar um instalador separado por módulo, se necessário, para reduzir ainda mais o tamanho.
- [ ] Ajustar o pacote final para excluir dependências não usadas por módulos desativados.
- [ ] Adicionar suporte a instalação silenciosa e automação de deploy.
- [x] Versionar melhor os instaladores gerados para facilitar o rollback.

## Qualidade e manutenção
- [x] Adicionar mais testes para o fluxo de instalação e para os widgets bloqueados. (lado Python: LockedModuleWidget, ModuleInstallWorker, VersionManager, safe_import; instalador Inno Setup em si fica fora do escopo do pytest)
- [x] Melhorar logs de instalação e execução para diagnóstico de problemas.
- [ ] Reorganizar o código em módulos ainda mais isolados para facilitar manutenção.
- [x] Revisar tratamento de erros em cenários de rede e falta de dependências. (feito no coupa_scraper.py; email_sender/download_scraper ficam para depois)

## Funcionalidades
- [ ] Implementar atualização automática de módulos individuais sem reinstalar o app inteiro.
- [x] Criar um painel de status mostrando quais módulos estão ativos e quais não foram instalados.
- [ ] Adicionar suporte a temas claro/escuro.
- [ ] Melhorar a experiência de importação/exportação de perfis e configurações.
