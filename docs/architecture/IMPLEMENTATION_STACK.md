# Implementation Stack — AIgnt OS

## Objetivo
Registrar a stack Python recomendada para implementar o AIgnt OS conforme a arquitetura definida.

## MVP
- **Python 3.12**
- **Typer** para CLI
- **Rich** para UX terminal
- **python-statemachine** para estados
- **engine própria de pipeline** em Python
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

### engine própria de pipeline
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
