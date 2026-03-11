# Implementation Stack — AIgnt OS

## Objetivo
Registrar a stack Python recomendada para implementar o AIgnt OS conforme a arquitetura definida.

## MVP
- **Python 3.12**
- **Docker + Compose** como requisito operacional inicial de execução prática
- **Typer** para CLI
- **Rich** para UX terminal
- **python-statemachine** para estados
- **AIgnt-Synapse-Flow** em Python como engine própria de pipeline
- **asyncio** para concorrência
- **asyncio.create_subprocess_exec()** para execução de CLIs
- **Pydantic v2** para contratos internos
- **pydantic-settings** para configuração
- **jsonschema** para validar SPEC
- **re + ast** para parsing e validação de código
- **SQLAlchemy 2 + SQLite** para persistência operacional
- **Alembic** para migrações
- **structlog** para logs estruturados
- **pytest + pytest-asyncio + pytest-mock + Hypothesis**
- **uv + Ruff + mypy**

## Justificativas principais
### Typer
Melhor DX para CLI moderna, type hints e uso assistido por IA.

### Docker + Compose
Padroniza o `DOCKER_PREFLIGHT`, isola a execução prática e reduz o risco de comandos perigosos no host.

Trade-offs:
- melhora isolamento e repetibilidade do ambiente;
- aumenta o custo operacional quando o Docker falha, inclusive para tarefas simples;
- desloca o início prático da feature para depois da validação do ambiente;
- exige que `repo-automation` prepare e valide o runtime antes de `spec-editor`.
- por isso, o preflight padrão deve permanecer leve (`compose config`), com build e runtime completo reservados para workflows ou execuções explícitas.

### AIgnt-Synapse-Flow
Permite controle fino de hand-offs, retry, rollback e estágios específicos do domínio sem complexidade operacional de um orquestrador pesado.

### python-statemachine
Expressa bem regras explícitas de transição.

### asyncio subprocess
Prepara o caminho para paralelismo sem reescrever adapters.

### SPEC híbrida
Melhora legibilidade para humanos e interpretação por IA, mantendo validação formal.

## Evolução futura
- PostgreSQL no lugar de SQLite.
- pgvector ou Qdrant para memória vetorial.
- Dramatiq ou Temporal quando houver workers distribuídos reais.
