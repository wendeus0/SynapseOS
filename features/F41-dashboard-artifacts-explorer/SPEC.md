---
id: F41-dashboard-artifacts-explorer
type: feature
summary: "Navegação e visualização de artefatos gerados na TUI"
inputs:
  - "Tecla 'a' ou navegação para aba Artifacts no Dashboard"
  - "Seleção de artefato na lista"
outputs:
  - "Painel com lista de arquivos em artifacts/"
  - "Modal ou painel de preview do conteúdo (para texto)"
  - "Exibição de metadados (para binários)"
acceptance_criteria:
  - "Deve listar todos os arquivos presentes no diretório de artefatos da run atual"
  - "Deve permitir selecionar um arquivo da lista"
  - "Deve exibir o conteúdo de arquivos de texto (txt, md, json, py, yaml) no visualizador"
  - "Deve exibir apenas metadados (nome, tamanho, path) para arquivos binários ou não suportados"
  - "Deve permitir retornar à lista de steps ou fechar o visualizador de artefatos"
  - "Deve atualizar a lista se novos artefatos forem gerados durante a execução (se a TUI suportar refresh)"
non_goals:
  - "Edição de arquivos"
  - "Renderização de imagens ou PDF na TUI"
  - "Download/Upload de arquivos via TUI"
  - "Delete de artefatos via TUI"
---

# Contexto

O AIgnt OS gera diversos artefatos durante a execução (código, relatórios, diagramas) no diretório `artifacts/`. Atualmente, para visualizar esses arquivos, o operador precisa sair da TUI ou abrir um segundo terminal. A feature F17 trouxe o preview via CLI (`runs show --artifact`), mas a experiência na TUI (F33/F39) ainda carece dessa integração.

# Objetivo

Expandir o Dashboard TUI para incluir um explorador de artefatos. O usuário poderá alternar entre a visão de Steps e a visão de Artefatos, listar os arquivos gerados pela run atual e visualizar o conteúdo de arquivos de texto diretamente na interface, mantendo o fluxo de trabalho concentrado no terminal principal.
