---
id: F44-auth-backend-abstraction
type: feature
summary: "Abstração do backend de autenticação para suportar múltiplos providers"
inputs:
  - Configuração de `auth_provider` em `AppSettings`
outputs:
  - Protocolo `AuthProvider`
  - Implementação `FileRegistryAuthProvider` (padrão atual)
  - Factory/Service para resolução do provider
acceptance_criteria:
  - "Definir interface abstrata `AuthProvider` com método `authenticate`"
  - "Refatorar lógica de arquivo JSON para `FileRegistryAuthProvider`"
  - "Configuração deve permitir selecionar o provider (default: 'file')"
  - "Manter compatibilidade com comandos existentes de `auth` CLI"
  - "Testes devem validar que o provider correto é instanciado via config"
non_goals:
  - Implementar providers externos (LDAP, OIDC) nesta fase
  - Alterar o formato do arquivo `auth.json` atual
  - Implementar RBAC granular (F47)
---

# Contexto

Atualmente, a lógica de autenticação está fortemente acoplada à classe `AuthRegistryStore`, que gerencia persistência em arquivo JSON e validação de tokens. Para suportar futuros mecanismos de autenticação (como tokens de ambiente, OIDC ou integração com Vault) na Fase 4, precisamos desacoplar a interface de verificação da implementação de armazenamento.

# Objetivo

Criar uma camada de abstração para o backend de autenticação. O sistema deve interagir com um `AuthProvider` genérico para validar credenciais, permitindo que a implementação subjacente seja trocada via configuração sem alterar o código consumidor (CLI/API). Nesta feature, extrairemos a implementação atual para `FileRegistryAuthProvider`.
