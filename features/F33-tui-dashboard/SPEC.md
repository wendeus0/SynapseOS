---
id: F33-tui-dashboard
type: feature
summary: "Adiciona dashboard TUI para monitoramento de runs em tempo real"
inputs:
  - "ID da run a monitorar (argumento obrigatório)"
  - "Intervalo de refresh (opcional, default 1s)"
outputs:
  - "Interface interativa no terminal exibindo estado, passos e logs da run"
  - "Encerramento limpo ao pressionar 'q' ou Ctrl+C"
acceptance_criteria:
  - "O comando `aignt runs watch <run_id>` deve abrir uma TUI sem travar a CLI"
  - "A TUI deve exibir o ID, Status Atual, Estado Atual e Spec Path da run"
  - "A TUI deve listar os steps já executados com ícones de status (✅, ❌, ⏳)"
  - "A TUI deve permitir visualizar detalhes do step selecionado"
  - "Layout moderno com painéis divididos (Sidebar/Content)"
  - "Uso de cores semânticas (Verde=Sucesso, Vermelho=Falha)"
  - "A TUI deve atualizar as informações automaticamente sem necessidade de input do usuário"
  - "A TUI deve permitir sair pressionando 'q'"
  - "Se a run não existir, deve exibir erro amigável e sair antes de iniciar a TUI"
non_goals:
  - "Interação complexa com a run (pausar/retomar/cancelar) nesta primeira versão"
  - "Visualização de logs em tempo real (streaming) - foco inicial em estado e steps"
  - "Suporte a mouse"
  - "Temas customizáveis"
---

# Contexto

Atualmente, o operador precisa executar repetidamente `aignt runs show <run_id>` ou usar `watch -n 1 ...` para acompanhar o progresso de uma run longa. Isso é ineficiente e oferece uma experiência de usuário pobre ("cega"), dificultando a identificação rápida de travamentos ou falhas.

# Objetivo

Implementar um comando `aignt runs watch` que exiba um dashboard textual (TUI) usando a biblioteca `textual`. O dashboard deve conectar-se ao banco de dados SQLite local em modo somente leitura (polling), exibindo o cabeçalho da run e a lista de steps conforme eles são persistidos pelo worker.
