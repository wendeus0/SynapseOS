---
id: F49-gemini-adapter
type: feature
summary: Implement a Gemini CLI adapter for Synapse OS.
inputs:
  - Gemini API Key
  - Prompt text
outputs:
  - CLIExecutionResult
acceptance_criteria:
  - Must implement BaseCLIAdapter protocol
  - Must execute successfully with valid mock/key
  - Must handle authentication errors
  - Must report operational failures correctly
non_goals:
  - Implementing full multi-modal support
  - Complex prompt engineering within the adapter
---

# Contexto

O AIgnt OS (Synapse OS) precisa demonstrar que sua arquitetura é agnóstica a provedores de LLM. Atualmente, existe apenas o `CodexCLIAdapter`. A adição de um `GeminiCLIAdapter` prova a extensibilidade do sistema e permite o uso de modelos do Google via CLI.

# Objetivo

Implementar `GeminiCLIAdapter` em `src/synapse_os/adapters.py`, herdando de `BaseCLIAdapter`. O adapter deve ser capaz de invocar uma ferramenta CLI fictícia ou real (ex: via `curl` ou wrapper python) que interaja com a API do Gemini, retornando um `CLIExecutionResult` padronizado.

Para fins deste MVP e testes, o adapter pode simular a chamada ou usar um script wrapper simples, focando no contrato da interface `BaseCLIAdapter`.
