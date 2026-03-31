---
id: F55-hook-cli-management
type: feature
summary: Adicionar comandos CLI para listar, ativar, desativar e validar hooks configurados no Synapse-Flow.
inputs:
    - AppSettings com hooks globais configurados
    - SPEC.md com hooks por run
    - HookDispatcher ja existente (F54)
outputs:
    - Comando synapse hooks list exibindo hooks globais e por SPEC
    - Comando synapse hooks validate testando importabilidade de handler
    - Comando synapse hooks status mostrando hooks ativos da ultima run
    - Saida estruturada em formato tabela via Rich
acceptance_criteria:
    - "Dado AppSettings com 2 hooks configurados, quando synapse hooks list e executado, entao exibe tabela com point, handler, failure_mode e enabled de cada hook"
    - "Dado handler com dotted path valido (ex: os.path.join), quando synapse hooks validate os.path.join e executado, entao exibe mensagem de sucesso com o nome da funcao importada"
    - "Dado handler com dotted path invalido (ex: nonexistent.func), quando synapse hooks validate nonexistent.func e executado, entao exibe erro com exit code 1"
    - "Dado SPEC.md com hooks no frontmatter, quando synapse hooks list --spec path e executado, entao exibe hooks globais e hooks da SPEC separadamente"
    - "Dado SPEC.md sem campo hooks, quando synapse hooks list --spec path e executado, entao exibe apenas hooks globais"
    - "Dado nenhum hook configurado, quando synapse hooks list e executado, entao exibe mensagem informativa indicando que nenhum hook esta configurado"
    - "Dado handler existente mas funcao inexistente no modulo, quando synapse hooks validate os.nonexistent_func e executado, entao exibe erro indicando que a funcao nao foi encontrada"
    - "Dado SPEC.md com hooks malformados, quando synapse hooks list --spec path e executado, entao exibe erro de validacao da SPEC"
non_goals:
    - Edicao de hooks via CLI (somente leitura e validacao)
    - Hot-reload de hooks em runtime
    - Hooks por usuario ou por workspace
    - Interface TUI para hooks
security_notes:
    - hooks validate importa o handler via importlib — executar apenas com dotted paths confiaveis
    - Nao executar handlers, apenas verificar importabilidade
---

# Contexto

A feature F54 implementou o HookDispatcher com suporte a hooks pre/post síncronos e assíncronos. Porém, não há forma de inspecionar ou validar hooks pela CLI — o operador precisa editar AppSettings ou SPEC.md manualmente e só descobre erros na execução.

# Objetivo

Adicionar comandos CLI de leitura e validação para hooks, permitindo que operadores inspecionem a configuração atual e validem handlers antes de executar pipelines.

## Escopo

Três subcomandos sob `synapse hooks`:

- `synapse hooks list [--spec <path>]` — lista hooks globais (AppSettings) e hooks por SPEC
- `synapse hooks validate <handler>` — testa se um dotted path é importável
- `synapse hooks status` — mostra hooks ativos da última run (se disponível)

## Fora de Escopo

Ver non_goals no frontmatter.

## Casos de Erro

- Handler inexistente → erro com exit code 1
- SPEC inválida → erro de validação com mensagem clara
- Nenhum hook configurado → mensagem informativa (não erro)
- Módulo existe mas função não → erro específico diferenciado de módulo não encontrado

## Artefatos Esperados

- `src/synapse_os/cli/hooks.py` (novo)
- `src/synapse_os/cli/app.py` (modificado: registrar subcomando hooks via app.add_typer)
- `tests/unit/test_hooks_cli.py` (novo)

## Observações para Planejamento

- Reutilizar Rich para formatação de tabelas (já dependência do projeto)
- `hooks validate` não executa o handler — apenas verifica importabilidade via importlib
- `hooks status` lê hooks_active do PipelineContext se houver run recente; caso contrário, exibe mensagem informativa

## Observações para Revisão

- Verificar que `hooks validate` não executa código do handler, apenas importa
- Verificar que exit codes são consistentes (0 = sucesso, 1 = erro)
- Verificar que mensagens de erro são distinguíveis para módulo vs função não encontrados
