---
id: F54-hook-system
type: feature
summary: Adicionar pontos de extensão controlados ao Synapse-Flow via hooks pre/post síncronos e assíncronos configuráveis por AppSettings e frontmatter SPEC.
inputs:
  - AppSettings com lista opcional de HookConfig (global)
  - frontmatter SPEC com lista opcional de HookConfig (override por run)
  - contexto de execução de cada step e transição de estado
outputs:
  - HookContext enriquecido retornado por dispatch_pre quando handler aplica context_patch
  - PipelineExecutionError levantado quando hook hard_fail rejeita step ou transição
  - StepResult com falha propagada ao supervisor quando hook supervisor_delegate rejeita
  - PipelineContext.hooks_active listando handlers efetivos após merge global+SPEC
  - SpecValidationError quando frontmatter SPEC contém hooks malformados
acceptance_criteria:
  - Dado AppSettings com HookConfig(point=pre_step, handler válido, failure_mode=hard_fail), quando PipelineEngine executa qualquer step, então o handler é invocado antes do step e pode bloquear a execução levantando PipelineExecutionError
  - Dado HookConfig com failure_mode=supervisor_delegate e handler que retorna allowed=False, quando PipelineEngine executa o step, então o step é marcado como falha e o supervisor é acionado sem propagar exceção direta
  - Dado HookConfig(point=post_step), quando step completa com sucesso ou falha, então o handler post é invocado de forma não-bloqueante e exceções do handler não propagam
  - Dado HookConfig(point=pre_state_transition, failure_mode=hard_fail) com handler que rejeita, quando PipelineEngine tenta avançar estado, então PipelineExecutionError é levantado e a transição não ocorre
  - Dado HookConfig(point=post_state_transition), quando transição de estado completa, então o handler é invocado de forma não-bloqueante
  - Dado handler com allowed=True e context_patch contendo uma chave extra, quando dispatch_pre retorna, então HookContext.metadata contém a chave com o valor do patch
  - Dado AppSettings.hooks com 1 global e SPEC.hooks desabilitando o mesmo handler+point, quando PipelineEngine executa, então o handler não é invocado e PipelineContext.hooks_active está vazio
  - Dado AppSettings.hooks com 1 global e SPEC.hooks adicionando 1 extra, quando PipelineEngine executa, então ambos os handlers aparecem em PipelineContext.hooks_active
  - Dado HookConfig com handler de dotted path inválido e failure_mode=hard_fail, quando HookDispatcher é construído, então RuntimeError é levantado imediatamente
  - Dado HookConfig com handler de dotted path inválido e failure_mode=supervisor_delegate, quando HookDispatcher é construído, então o hook é desabilitado silenciosamente com warning no log
  - Dado frontmatter SPEC com campo hooks contendo point inválido, quando validate_spec_file é chamado, então SpecValidationError é levantado com mensagem mencionando hooks
  - Dado PipelineEngine com HookDispatcher configurado, quando run() completa até SPEC_VALIDATION, então ctx.hooks_active contém os handlers efetivos
non_goals:
  - Hooks extensíveis por usuário final via plugin marketplace
  - Hook scheduling (cron, delay)
  - Hooks em modo assíncrono bloqueante
  - Override de hooks por variável de ambiente por run (somente AppSettings + SPEC)
  - Validação de importabilidade de handlers no spec-validator (somente no dispatcher)
security_notes:
  - handlers são importados via importlib — dotted paths devem ser confiáveis; não há sandbox
  - hard_fail handlers com import inválido falham na startup (fail-fast)
---

# Contexto

O SynapseOS pós-F53 possui foundations sólidas: ToolSpec/capabilities (F51), workspace isolation (F52) e observability com run_events (F53). O próximo passo é expor pontos de extensão controlados no Synapse-Flow — hooks que permitem injetar lógica de guarda, custo, permissão e observabilidade sem modificar o núcleo da pipeline.

Os hooks seguem o modelo do Hook System do Claude Code (PreToolUse, PostToolUse, SessionStart) adaptado para o modelo state-driven do Synapse-Flow: pré-hooks são síncronos e podem bloquear; pós-hooks são assíncronos fire-and-forget.

# Objetivo

Implementar um HookDispatcher que carrega handlers via importlib, faz merge de hooks globais (AppSettings) com hooks por run (frontmatter SPEC) e despacha nos quatro pontos de extensão da pipeline: pre_step, post_step, pre_state_transition, post_state_transition. O PipelineEngine consome o dispatcher como dependência opcional injetada.

## Escopo

Quatro pontos de hook expostos no Synapse-Flow:

- `pre_step` — síncrono, antes de executar qualquer step (PLAN, TEST_RED, CODE_GREEN, etc.)
- `post_step` — assíncrono fire-and-forget, após step completar (sucesso ou falha)
- `pre_state_transition` — síncrono, antes de avançar estado na state machine
- `post_state_transition` — assíncrono fire-and-forget, após transição confirmada

Contratos novos em runtime_contracts.py: HookConfig, HookContext, HookResult.

HookDispatcher em src/synapse_os/hooks.py com: _merge (global+SPEC), _load_handlers (importlib), dispatch_pre (síncrono, levanta HookRejectedError), dispatch_post (thread daemon).

AppSettings ganha campo hooks: list[HookConfig]. SpecMetadata ganha campo hooks: list[HookConfig]. PipelineContext ganha hooks_active: list[str].

## Fora de Escopo

Ver non_goals no frontmatter.

## Casos de Erro

- Handler com dotted path inválido e failure_mode=hard_fail → RuntimeError na construção do HookDispatcher (fail-fast na startup)
- Handler com dotted path inválido e failure_mode=supervisor_delegate → warning no log, hook desabilitado para a run, execução continua normalmente
- Handler pre_step retorna allowed=False com failure_mode=hard_fail → PipelineExecutionError com mensagem "Hook rejected step '...':"
- Handler pre_step retorna allowed=False com failure_mode=supervisor_delegate → RetryableStepError propagado ao supervisor
- Handler post_step levanta exceção → warning no log, exceção swallowed, execução não interrompida
- frontmatter SPEC com hooks malformados (point inválido, handler ausente) → SpecValidationError com referência ao campo hooks

## Artefatos Esperados

- src/synapse_os/hooks.py (novo)
- src/synapse_os/runtime_contracts.py (modificado: +HookConfig, +HookContext, +HookResult)
- src/synapse_os/config.py (modificado: +hooks em AppSettings)
- src/synapse_os/specs/validator.py (modificado: +hooks em SpecMetadata)
- src/synapse_os/pipeline.py (modificado: +hook_dispatcher param, +_run_step_with_hooks, +_advance_with_hooks)
- tests/unit/test_hook_contracts.py (novo)
- tests/unit/test_hook_dispatcher.py (novo)
- tests/unit/test_spec_validator_hooks.py (novo)
- tests/unit/test_pipeline_hook_integration.py (novo)
- tests/integration/test_hook_system_e2e.py (novo)

## Observações para Planejamento

- PipelineEngine.run() é síncrono; dispatch_post usa threading.Thread(daemon=True) para não bloquear
- SynapseStateMachine fica PURA — hooks de transição são gerenciados pelo PipelineEngine via _advance_with_hooks
- Handlers são importados uma vez na construção do dispatcher, não a cada dispatch
- _join_post_handlers() deve existir no dispatcher para determinismo em testes

## Observações para Revisão

- Verificar que exceções de post handlers não propagam em nenhum path de execução
- Verificar que hard_fail com import inválido falha na construção, não na primeira chamada
- Verificar que merge respeita: disable (enabled=False) remove por handler+point, não só por handler
