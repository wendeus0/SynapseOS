# ADR-014 — Adotar HTTP Control Plane com FastAPI

## Status

Aceito

## Contexto

O SynapseOS opera primariamente via CLI com runtime dual (CLI efêmero + worker residente), mas precisa de uma interface programática para:

- Integração com ferramentas externas que preferem APIs REST;
- Monitoramento e observabilidade remota das runs;
- Trigger de runs via webhooks;
- Consulta de estado e artefatos sem acesso direto ao filesystem.

A arquitetura atual é state-driven com state machine explícita (ADR-003) e Synapse-Flow como engine de pipeline, tornando natural expor estados e transições via API.

## Decisão

Adotar um **HTTP Control Plane** usando FastAPI como camada de interface REST sobre o Synapse-Flow.

Componentes:

- **FastAPI** como framework web (async nativo, validação Pydantic, OpenAPI automático);
- **REST API design** com recursos principais: `/health`, `/api/v1/runs`, `/api/v1/runtime/status`, `/api/v1/artifacts/{run_id}`;
- **Async handlers** para não bloquear o event loop do worker;
- **State machine projection** — estados internos expostos como endpoints de consulta;
- **Auth middleware** com Bearer token (`SYNAPSE_OS_API_TOKEN`), health check é público.

O HTTP Control Plane é uma **camada opcional** — o sistema continua funcionando 100% via CLI sem a API ativa. A API é ativada via comando explícito `synapse control-plane start`.

## Consequências

### Positivas

- Permite integração com sistemas externos que esperam APIs REST;
- Facilita observabilidade e dashboards sem acesso ao host;
- Async/await alinhado com o modelo async do Synapse-Flow;
- OpenAPI/Swagger gerado automaticamente para documentação;
- Separação clara: lógica de negócio no Synapse-Flow, protocolo HTTP na camada de controle.

### Negativas

- Adiciona dependência FastAPI + Uvicorn;
- Requer modelagem explícita de DTOs para evitar expor objetos internos;
- Risco de acoplamento se lógica de negócio vazar para handlers HTTP;
- Necessidade de autenticação/autorização para exposição em rede.

## Alternativas consideradas

- **gRPC**: rejeitado — maior complexidade, necessidade de proto files, menor aderência a integrações simples;
- **GraphQL**: rejeitado — overkill para MVP, complexidade de resolvers e N+1 queries;
- **Sem API HTTP**: rejeitado — limitaria integrações e observabilidade remota;
- **Flask/Sanic**: rejeitado — FastAPI tem melhor suporte a async, tipagem e documentação automática.

## Relação com ADRs existentes

- ADR-003 (state-machine-pipeline-engine): API reflete estados da state machine;
- ADR-009 (runtime-dual): API é interface do worker residente leve;
- ADR-010 (synapse-flow-name): API expõe operações do Synapse-Flow.
