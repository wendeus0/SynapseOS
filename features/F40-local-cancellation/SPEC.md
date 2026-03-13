---
id: F40-local-cancellation
type: feature
summary: "Cancelamento local de runs via CLI e TUI com sinalização de graceful shutdown."
inputs:
  - "Comando CLI `aignt runs cancel <run_id>`"
  - "Atalho de teclado no dashboard TUI (ex: 'k')"
outputs:
  - "Run transita para estado `cancelling` e depois `cancelled`"
  - "Mensagem de confirmação na interface"
acceptance_criteria:
  - "Deve ser possível cancelar uma run em estado `running` ou `pending` via CLI"
  - "Deve ser possível cancelar a run atualmente visualizada no dashboard via atalho de teclado"
  - "O worker deve detectar o sinal de cancelamento antes de iniciar o próximo step"
  - "O estado final da run deve ser persistido como `cancelled`"
  - "Tentativa de cancelar run já finalizada deve retornar erro ou aviso informativo"
non_goals:
  - "Cancelamento distribuído em múltiplos hosts"
  - "Interrupção forçada (`kill -9`) de subprocessos externos (graceful stop apenas)"
  - "Filas de cancelamento remoto ou scheduler complexo"
---

# Contexto

Atualmente, uma run iniciada no AIgnt OS (especialmente em modo `worker` residente) só para quando termina todos os steps ou falha. Se o usuário perceber um erro ou mudar de ideia durante uma execução longa, a única opção é matar o processo do worker/CLI, o que pode deixar o estado inconsistente (`running` para sempre no banco) ou corromper arquivos. É necessário um mecanismo oficial para solicitar a interrupção.

# Objetivo

Implementar o suporte a cancelamento local de runs. O mecanismo funcionará via sinalização no banco de dados (flag ou estado) que o worker consulta periodicamente.
- **CLI**: Novo comando para marcar a run como cancelada.
- **TUI**: Atalho para chamar esse comando para a run atual.
- **Runtime**: Lógica no loop do worker para checar "devo parar?" antes de cada step.

Isso garante que o cancelamento seja limpo, permitindo que o worker feche recursos e atualize o estado final corretamente para `cancelled`.
