---
applyTo: ".github/workflows/*.yml"
---

# CI/CD — Instruções de contexto

## Regra fundamental

**Nunca remova ou desative um gate existente sem justificativa explícita e aprovação.**
Os workflows são a linha de defesa operacional do repositório.

## Gates obrigatórios (não modificar sem justificativa)

| Job | Propósito |
|-----|-----------|
| `branch-validation` | Valida nome e alinhamento da branch com `origin/main` |
| `repo-checks` | Ruff format, ruff check, mypy, pytest |
| `docker-preflight` | Valida `compose config` no caminho leve; build fica explícito nos jobs de imagem |
| `security-review` | Gate de segurança antes de merge |
| `build-image` | Build da imagem Docker de produção |

## Estrutura dos workflows existentes

- `operational-ci.yml`: jobs `branch-validation`, `docker-preflight`, `repo-checks`, `security-review`
- `container-build.yml`: job `build-image`
- `runtime-integration.yml`: testes de integração do runtime

## Convenções

- Nomes de jobs: `kebab-case`
- Runner: `ubuntu-latest`
- Python via `uv` — não use `setup-python` + `pip install`
- Segredos via `${{ secrets.NOME }}` — nunca exponha valores em logs
- Use `env:` para variáveis de ambiente em vez de inline no `run:`

## Modificações permitidas sem confirmação

- Atualizar versões de actions (`actions/checkout@v4` → `@v5`)
- Adicionar steps de diagnóstico/log que não afetam o gate
- Ajustar `timeout-minutes` quando justificado

## Modificações que requerem confirmação

- Adicionar ou remover jobs
- Alterar `on:` triggers
- Modificar condições de falha de qualquer gate
- Alterar a ordem de dependência entre jobs (`needs:`)
- Adicionar `continue-on-error: true` em qualquer job

## Regras de branch nos workflows

O `validate-branch.sh` verifica:
1. Nome da branch segue convenção (`feature/`, `fix/`, `chore/`, `feat/`, `docs/`)
2. Branch está alinhada com `origin/main` (sem behind)

Nunca modifique a lógica de validação de branch sem atualizar o script correspondente.
