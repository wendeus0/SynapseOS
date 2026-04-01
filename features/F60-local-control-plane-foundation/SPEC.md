---
id: F60-local-control-plane-foundation
type: feature
summary: Local HTTP API layer exposing SynapseOS core operations programmatically via FastAPI on localhost.
inputs:
    - SPEC.md with feature requirements
    - Existing RunRepository, RuntimeService, ArtifactStore
outputs:
    - FastAPI control plane server with REST endpoints
    - Auth middleware for API token validation
    - CLI commands for control plane management
acceptance_criteria:
    - GET /health returns 200 with runtime status
    - POST /api/v1/runs creates a run and returns 201
    - GET /api/v1/runs lists runs with pagination
    - POST /api/v1/runs/{run_id}/cancel marks run as cancelled
    - Auth middleware blocks unauthorized requests with 401 when API-token auth is enabled
    - All unit tests pass
non_goals:
    - WebSocket streaming
    - External network binding
    - Web dashboard
---

# Contexto

Atualmente o SynapseOS só pode ser controlado via CLI (`synapse` command). Não existe interface programática para submeter runs remotamente, consultar status em tempo real, monitorar o runtime, cancelar runs ou listar artefatos gerados.

# Objetivo

Criar uma camada de API HTTP local (localhost-only) que exponha as operações core do SynapseOS de forma programática, permitindo integração com ferramentas externas sem depender exclusivamente da CLI.

## Escopo

### In scope

- Servidor HTTP leve com FastAPI
- Bind exclusivo em `127.0.0.1` (localhost-only, sem exposição externa)
- Endpoints REST para operações core:
    - `GET /health` — health check do runtime
    - `GET /api/v1/runs` — listar runs com paginação
    - `POST /api/v1/runs` — submeter nova run
    - `GET /api/v1/runs/{run_id}` — detalhe de uma run
    - `POST /api/v1/runs/{run_id}/cancel` — cancelar run pendente/em execução
    - `GET /api/v1/runtime/status` — status do runtime residente
    - `GET /api/v1/artifacts/{run_id}` — listar artefatos de uma run
- Middleware de autenticação via token (reutilizar auth existente)
- CORS desabilitado por padrão (localhost-only)

### Out of scope

- Interface web / dashboard HTTP
- WebSocket para streaming em tempo real
- Exposição externa (bind em 0.0.0.0)
- gRPC ou outros protocolos
- Multi-tenant ou isolamento por workspace via API
- Upload de arquivos via API

## Critérios de Aceite

### AC1: Servidor HTTP inicia e responde

- `synapse control-plane start` inicia o servidor em `127.0.0.1:8080` (porta configurável)
- `GET /health` retorna `{"status": "ok", "runtime": "running|stopped"}` com status 200
- `GET /health` retorna status 503 se o runtime não estiver disponível

### AC2: Listar runs via API

- `GET /api/v1/runs` retorna lista paginada de runs
- Suporta query params `?limit=20&offset=0`
- Retorna JSON com estrutura `{runs: [...], total: N, limit: N, offset: N}`
- Cada run inclui: `id`, `status`, `created_at`, `prompt` (truncado)

### AC3: Submeter run via API

- `POST /api/v1/runs` aceita `{"prompt": "..."}` e opcionalmente `{"mode": "sync|async|auto"}`
- Retorna `201 Created` com `{"run_id": "...", "status": "pending"}`
- Retorna `422` se prompt estiver vazio ou ausente
- Run submetida via API é persistida no mesmo SQLite e consumida pelo worker

### AC4: Detalhe de run via API

- `GET /api/v1/runs/{run_id}` retorna detalhe completo da run
- Retorna `404` se run não existir
- Inclui: `id`, `status`, `prompt`, `created_at`, `updated_at`, `steps`, `artifacts`

### AC5: Cancelar run via API

- `POST /api/v1/runs/{run_id}/cancel` marca run como cancelada
- Retorna `200` se cancelamento for bem-sucedido
- Retorna `409` se run já estiver em estado terminal (completed/failed/cancelled)
- Retorna `404` se run não existir

### AC6: Status do runtime via API

- `GET /api/v1/runtime/status` retorna estado do runtime residente
- Inclui: `pid`, `uptime`, `state`, `active_runs`, `pending_runs`

### AC7: Listar artefatos via API

- `GET /api/v1/artifacts/{run_id}` lista artefatos gerados
- Retorna `404` se run não existir
- Retorna lista com `{name, size_bytes, created_at, type}` para cada artefato

### AC8: Autenticação por token

- Token pode ser configurado via env `SYNAPSE_API_TOKEN` ou config
- Requests sem token válido retornam `401 Unauthorized` quando auth por token estiver habilitada
- Health check (`/health`) é público (sem auth)
- Se `SYNAPSE_API_TOKEN` não estiver definido, auth é desabilitada (modo dev)

### AC9: Porta configurável

- Porta padrão: `8080`
- Configurável via `--port` flag ou env `SYNAPSE_CONTROL_PORT`
- Host padrão: `127.0.0.1`
- Host configurável via `--host` flag (com warning se não for localhost)

### AC10: CLI command para gerenciar control plane

- `synapse control-plane start` — inicia servidor
- `synapse control-plane stop` — para servidor
- `synapse control-plane status` — mostra status

## Design Técnico

### Arquitetura

```
[CLI: synapse control-plane start]
         |
         v
[ControlPlaneServer] -- FastAPI app
         |
         +--> /health         --> RuntimeService.ready()
         +--> /api/v1/runs    --> RunRepository (SQLite)
         +--> /api/v1/runtime --> RuntimeService
         +--> /api/v1/artifacts --> ArtifactStore
```

### Módulos novos

- `src/synapse_os/control_plane/__init__.py`
- `src/synapse_os/control_plane/server.py` — FastAPI app + endpoints
- `src/synapse_os/control_plane/models.py` — Pydantic models para request/response
- `src/synapse_os/control_plane/middleware.py` — Auth middleware
- `src/synapse_os/control_plane/cli.py` — Typer subcommands

### Dependências novas

- `fastapi>=0.115.0`
- `uvicorn>=0.32.0`

### Reutilização

- `RunRepository` de `persistence.py`
- `RuntimeService` de `runtime/service.py`
- `ArtifactStore` de `persistence.py`
- Auth token validation de `auth.py`

## Riscos e Mitigações

| Risco                               | Mitigação                                                          |
| ----------------------------------- | ------------------------------------------------------------------ |
| FastAPI adiciona dependência pesada | FastAPI é leve; uvicorn é dependency mínima                        |
| Exposição acidental externa         | Default hardcoded em 127.0.0.1; warning explícito se host mudar    |
| Conflito de porta                   | Mensagem clara de "port in use" no CLI                             |
| Auth bypass                         | Health check é o único endpoint público; middleware bloqueia resto |

## Testes

- Testes unitários de cada endpoint com `httpx.AsyncClient` + `TestApp`
- Testes de autenticação (com/sem token, token inválido)
- Testes de erro (404, 409, 422)
- Testes de integração com RunRepository mockado
- Testes de health check com runtime running/stopped

## Próximos Passos (pós-F60)

- WebSocket para streaming de logs em tempo real
- Dashboard web leve
- API para gestão de hooks
- API para gestão de adapters
