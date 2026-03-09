# NOTES — F11-repo-automation

## Decisões locais

- `compose.yaml` foi preferido em vez de `docker-compose.yml` por ser o formato recomendado atual e suficiente para o MVP.
- O rebuild local usa fingerprint de arquivos relevantes para evitar rebuild desnecessário sem depender de watcher residente.
- Os hooks Git ficam em `.githooks/` e só são ativados por `scripts/install-git-hooks.sh` para manter o fluxo opt-in e auditável.
- A validação contra `main` usa `origin/main` quando disponível e cai para `main` local se a referência remota não estiver acessível.
- Os scripts Docker exportam `DOCKER_CONFIG` para `.cache/docker/config` a fim de evitar dependência de escrita em `$HOME` e manter a operação reprodutível no workspace.

## Lacunas assumidas

- Não houve execução real de GitHub Actions; os workflows foram gerados prontos para uso.
- O serviço atual continua efêmero no container porque a CLI mínima ainda não implementa worker residente do runtime dual do MVP.

## Segurança

- Scripts operacionais evitam `eval` e comandos implícitos.
- O fluxo local bloqueia commits na `main` por padrão.
- Agents/Skills ainda não entram nos hooks; quando entrarem, devem ser tratados como entrada não confiável e rodar apenas por chamadas explícitas.
