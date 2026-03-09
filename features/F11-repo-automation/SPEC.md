---
id: F11-repo-automation
type: feature
summary: Implementar a infraestrutura operacional de containerização e automação do repositório para subir o AIgnt OS em Docker e validar fluxo de branch/commit.
workspace: .
inputs:
  - repository_structure
  - project_architecture_docs
  - operational_request_for_container_and_automation
outputs:
  - Dockerfile
  - .dockerignore
  - compose_runtime_definition
  - scripts_operacionais
  - github_workflows
constraints:
  - manter escopo estritamente operacional
  - preservar arquitetura CLI-first e MVP atual
  - não alterar lógica de produto além do necessário para subir container
  - não depender de acesso real ao Docker daemon ou GitHub para gerar os arquivos
  - não automatizar push direto para main
acceptance_criteria:
  - Existe Dockerfile funcional para subir a CLI mínima do projeto em container.
  - Existe arquivo de ignore de build Docker adequado ao contexto atual do repositório.
  - Existe definição de compose compatível com o MVP para executar a aplicação localmente.
  - Existem scripts em scripts/ para build, rebuild, validação contra main e checks de commit.
  - Existe ao menos um workflow de CI operacional e um workflow de build de container por mudanças relevantes.
  - O rebuild considera src/**, pyproject.toml, uv.lock, Dockerfile, compose.yaml ou docker-compose.yml, scripts/** e arquivos de configuração/runtime que afetem a imagem.
  - O fluxo operacional bloqueia uso direto da main por padrão e falha de forma clara quando a branch estiver desatualizada em relação à base configurada.
  - Há documentação local de riscos e mitigação de segurança para workflows, scripts e entrada futura de Agents/Skills no fluxo operacional.
non_goals:
  - alterar a engine própria de pipeline
  - implementar worker do runtime dual
  - adicionar lógica de domínio fora do bootstrap da CLI
  - publicar imagem em registry
  - criar plataforma de automação externa ao repositório
security_notes:
  - minimizar permissões de workflow
  - não embutir segredos em scripts ou container
  - evitar execução arbitrária implícita em hooks
  - tratar Agents/Skills como entradas não confiáveis quando entrarem no fluxo operacional
---

## 1. Contexto

O AIgnt OS já possui bootstrap mínimo em Python, mas ainda não possui camada operacional pronta para containerização, build repetível, rebuild baseado em mudanças relevantes e validações de branch/commit compatíveis com um fluxo seguro de repositório.

## 2. Objetivo

Entregar a infraestrutura operacional mínima para:
- subir a aplicação em Docker;
- automatizar build e rebuild;
- validar alinhamento da branch corrente com `main`;
- preparar fluxo local de commit/checks;
- fornecer workflows prontos para uso em GitHub Actions.

## 3. Escopo

Esta feature cobre apenas:
- `Dockerfile`;
- `.dockerignore`;
- `compose.yaml`;
- scripts operacionais em `scripts/`;
- hooks locais opcionais instaláveis;
- workflows em `.github/workflows/`;
- testes operacionais para os scripts.

## 4. Fora de Escopo

Fica explicitamente fora desta feature:
- mudanças na engine própria de pipeline;
- worker leve do runtime dual;
- novos adapters reais;
- lógica de produto além da subida da CLI mínima;
- publicação automática de imagem;
- automações dependentes de segredos externos.

## 5. Regras Funcionais

1. O container deve executar a CLI `aignt` sem depender de componentes ainda não implementados.
2. O build local deve ser acionável por script auditável.
3. O rebuild deve considerar mudanças em arquivos relevantes para imagem e runtime operacional.
4. A validação contra `main` deve ser explícita e configurável.
5. O fluxo de commit deve impedir uso direto de `main` por padrão.
6. Hooks locais devem ser opt-in via script de instalação.
7. Os workflows devem usar permissões mínimas e não devem tentar publicar artefatos externos no MVP.

## 6. Casos de Erro

- Ausência de Docker CLI deve gerar erro claro nos scripts de build reais.
- Ausência de referência `origin/main` deve cair para `main` local quando possível.
- Branch atrás da base deve falhar na validação operacional.
- Mensagem de commit fora do padrão deve falhar no hook `commit-msg`.

## 7. Critérios de Aceite Detalhados

### AC1. Container
- Existe `Dockerfile` compatível com Python 3.12.
- A imagem instala o projeto e expõe `aignt --help` como comando padrão verificável.

### AC2. Build/Rebuild
- Existe script de build explícito.
- Existe script de rebuild com detecção de mudanças relevantes por fingerprint ou diff equivalente.

### AC3. Branch/Main
- Existe script de validação contra `main` ou `origin/main`.
- A validação falha quando a branch está desatualizada.

### AC4. Commit flow
- Existe script de checks operacionais locais.
- Existe validação de mensagem de commit.
- Existe forma simples de instalar hooks locais sem alterar Git global.

### AC5. Segurança
- Workflows usam permissões mínimas.
- Riscos e mitigação ficam registrados em `NOTES.md`.

## 8. Artefatos Esperados

- `features/F11-repo-automation/SPEC.md`
- `features/F11-repo-automation/NOTES.md`
- `Dockerfile`
- `.dockerignore`
- `compose.yaml`
- `scripts/`
- `.githooks/`
- `.github/workflows/`
- testes operacionais em `tests/`

## 9. Observações para Planejamento

- Preferir shell simples e auditável.
- Tratar `uv.lock` como arquivo relevante de runtime/build.
- Permitir execução local sem Docker daemon apenas até o ponto de dry-run e validação estática.
