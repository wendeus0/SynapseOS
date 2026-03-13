---
id: F47-advanced-rbac
type: feature
summary: "Implementação de controle de acesso baseado em papéis (RBAC) para comandos da CLI"
inputs:
  - "Flag --role no comando aignt auth issue"
  - "Configuração de papéis e permissões no AuthRegistryStore"
outputs:
  - "Tokens vinculados a papéis específicos (admin, operator, viewer)"
  - "Erro de permissão (403/Forbidden) ao tentar executar comando não autorizado"
acceptance_criteria:
  - "Deve ser possível emitir token com papel específico via CLI (ex: --role viewer)"
  - "Token com papel 'viewer' deve conseguir listar/ver runs mas falhar ao tentar submit ou stop"
  - "Token com papel 'operator' deve conseguir gerenciar runs e runtime"
  - "Token com papel 'admin' deve ter acesso irrestrito"
  - "O default para novos tokens deve ser 'admin' para compatibilidade (ou 'operator'? Melhor manter admin por enquanto para não quebrar fluxo existente)"
  - "A verificação de permissão deve ocorrer antes da execução da lógica do comando"
non_goals:
  - "Interface gráfica para gestão de papéis"
  - "Papéis customizados definidos pelo usuário (apenas fixos no código por enquanto)"
  - "Hierarquia complexa de herança de permissões"
---

## Contexto

Atualmente, a autenticação no AIgnt OS é binária: ou o cliente possui um token válido e tem acesso total (sujeito apenas a restrições de `initiated_by` para operações de runtime), ou não tem acesso. Com a evolução para um modelo multi-usuário ou multi-agente, é necessário limitar o raio de ação de certos tokens (ex: um dashboard de visualização não deve poder parar o runtime).

## Objetivo

Implementar um sistema de RBAC (Role-Based Access Control) nativo na CLI.

### Mudanças Principais

1.  **Modelo de Dados**:
    -   Estender `AuthRegistryStore` para armazenar o `role` associado a cada `token_hash`.
    -   Definir enumeração de `AuthRole` (`ADMIN`, `OPERATOR`, `VIEWER`).
    -   Mapear `AuthRole` para lista de `Permission` (strings como `run:read`, `run:write`, `runtime:manage`, `auth:manage`).

2.  **CLI de Auth**:
    -   Adicionar opção `--role` ao comando `aignt auth issue`.

3.  **Enforcement**:
    -   Atualizar `Authenticator` ou `RequireAuth` para validar permissões exigidas por cada comando.
    -   Decorar comandos da CLI com `@require_permission(...)` ou similar.

4.  **Roles Iniciais**:
    -   `viewer`: Acesso a `runs list`, `runs show`, `doctor`, `version`.
    -   `operator`: Acesso a `viewer` + `runs submit`, `runtime start/stop/run`.
    -   `admin`: Acesso total, incluindo `auth manage`.

### Compatibilidade

-   Tokens existentes (sem role definido no JSON) serão tratados como `admin` para não quebrar ambientes em uso.
