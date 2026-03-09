---
id: f01-bootstrap-contracts
title: Bootstrap do projeto e contratos iniciais
type: feature
status: draft
owner: wendeus0
priority: p0
estimated_size: S
related_docs:
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
related_adrs:
  - docs/adr/002-python-orchestrator.md
  - docs/adr/003-state-machine-pipeline-engine.md
  - docs/adr/004-cli-adapter-layer.md
  - docs/adr/008-spec-driven-development.md
  - docs/adr/009-runtime-dual-cli-worker.md
acceptance_criteria:
  - O projeto instala e executa via pyproject.toml sem erro estrutural.
  - Existe um comando CLI mínimo do pacote aignt_os que responde sem falhar.
  - Existem modelos/contratos iniciais para TaskRequest, RunContext, CLIExecutionResult e ParsedArtifact.
  - Existe configuração básica centralizada para a aplicação.
  - Existe ao menos um teste automatizado para CLI mínima e um teste para contratos/modelos.
  - A organização do código respeita src/aignt_os e tests/.
inputs:
  - Estrutura base do repositório
  - Documentação arquitetural existente
outputs:
  - Scaffold Python mínimo funcional
  - CLI mínima
  - Modelos base do domínio
  - Configuração base
  - Testes iniciais
dependencies: []
out_of_scope:
  - Implementação completa da engine própria de pipeline
  - State machine funcional completa
  - Parsing robusto completo
  - Worker/daemon funcional
  - Persistência SQLite
  - Integração com agentes externos reais
---

# Contexto
Esta feature cria a base mínima de código para permitir o início do desenvolvimento guiado por SPEC e TDD no AIgnt OS.

# Objetivo
Estabelecer o primeiro incremento funcional do projeto em Python com CLI mínima e contratos estruturais do domínio.

# Escopo
## Incluído
- scaffold inicial do pacote `aignt_os`
- ponto de entrada mínimo da CLI
- modelos base do domínio
- configuração inicial
- testes básicos

## Fora de escopo
- pipeline de execução real
- runtime dual funcional
- adapters reais
- memória operacional persistente
- relatórios de execução completos

# Requisitos funcionais
1. O comando `aignt` deve iniciar sem erro estrutural.
2. A CLI mínima deve oferecer uma resposta simples de diagnóstico ou placeholder.
3. O sistema deve expor contratos iniciais fortemente tipados.
4. O projeto deve ter testes automatizados mínimos.

# Requisitos não funcionais
- Código simples, pequeno e legível.
- Nenhuma abstração prematura.
- Compatível com Python 3.12.
- Preparado para expansão futura sem inflar o escopo atual.

# Casos de erro
- Import path incorreto do pacote
- Configuração inválida
- Modelos inconsistentes
- CLI não inicializa

# Critérios de aceite detalhados
- `pytest` executa ao menos os testes da feature com sucesso quando a implementação estiver concluída.
- A CLI mínima retorna saída previsível.
- Os modelos aceitam dados válidos e rejeitam dados inválidos quando aplicável.
- O código permanece restrito ao escopo da feature.

# Observações
Esta feature existe para reduzir atrito nas próximas features. Ela não deve tentar “adiantar” pipeline, worker ou parsing real.
