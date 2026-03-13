# Relatório de Execução - F44 Auth Backend Abstraction

## Resumo
Abstração do backend de autenticação para permitir a integração futura com múltiplos provedores de identidade (IDPs), mantendo a compatibilidade com o registro local baseado em arquivo.

## Alterações Realizadas

### 1. Configuração
- Adicionado campo `auth_provider` em `AppSettings` (default: "file").
- Validado via Pydantic para garantir apenas valores suportados.

### 2. Core de Autenticação (`src/aignt_os/auth.py`)
- Definido protocolo `AuthProvider` com método `authenticate`.
- Implementada factory `get_auth_provider(settings)` para resolver a implementação correta.
- `AuthRegistryStore` agora satisfaz implicitamente o protocolo `AuthProvider`.

### 3. CLI (`src/aignt_os/cli/app.py`)
- Refatorado `_resolve_principal_id` para utilizar a factory `get_auth_provider`.
- Comandos de gerenciamento de tokens (`auth init`, `auth issue`, `auth disable`) agora verificam se o provider ativo suporta gerenciamento local (atualmente restrito a "file").

### 4. Testes
- Criado `tests/unit/test_auth_abstraction.py` verificando:
  - Conformidade de `AuthRegistryStore` com o protocolo.
  - Resolução correta da factory baseada na configuração.
  - Tratamento de erro para providers desconhecidos.
  - Fluxo de autenticação via interface abstrata.

## Validação
- Suite de testes de unidade: **PASS** (4 novos testes).
- Regressão completa (`commit-check.sh`): **PASS** (424 testes).

## Próximos Passos
- Implementar providers reais na Fase 4 (F47+), como variáveis de ambiente ou OIDC.
- A abstração atual já permite plugar esses novos backends sem alterar a CLI.
