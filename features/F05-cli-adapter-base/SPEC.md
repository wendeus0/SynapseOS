---
id: F05-cli-adapter-base
type: feature
summary: Implementar o adapter base assíncrono para executar ferramentas CLI com contrato único de resultado, timeout e sanitização leve de streams.
workspace: .
inputs:
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/adr/004-cli-adapter-layer.md
  - features/F04-parsing-engine-mvp/SPEC.md
  - features/F04-parsing-engine-mvp/NOTES.md
outputs:
  - base_cli_adapter_async
  - cli_execution_result_contract
  - timeout_handling
  - stdout_stderr_capture
  - adapter_unit_tests
constraints:
  - manter escopo estritamente no adapter base async e no contrato de execucao
  - nao implementar adapter real de ferramenta externa
  - nao mover regras de parsing da F04 para dentro do adapter
  - preservar separacao entre output bruto e output limpo
  - usar asyncio com create_subprocess_exec para subprocessos
acceptance_criteria:
  - Existe um BaseCLIAdapter assíncrono com contrato explícito para subclasses definirem o comando a executar.
  - Existe um CLIExecutionResult tipado que cobre tool_name, command, return_code, stdout_raw, stderr_raw, stdout_clean, stderr_clean, duration_ms, timed_out e success.
  - A execução do adapter captura stdout e stderr, sanitiza ANSI sem destruir o output bruto original e devolve resultado estruturado.
  - O adapter trata timeout de forma verificável, marca timed_out, encerra o processo e retorna resultado consistente.
  - Os testes cobrem caminho de sucesso, retorno não-zero, timeout e sanitização básica de streams.
non_goals:
  - integrar tool real
  - implementar pipeline linear, worker ou supervisor
  - reimplementar parsing profundo, extração de artefatos ou remoção de ruído operacional além de ANSI
  - adicionar retries, backoff ou streaming de subprocesso
  - executar validacao pratica dependente de Docker
dependencies:
  - F04-parsing-engine-mvp
---

# Contexto

Depois da F04, o AIgnt OS já possui um Parsing Engine MVP para separar output bruto, output limpo e artefatos. O próximo incremento natural do núcleo é fechar a camada base de execução CLI assíncrona, seguindo o ADR-004 e o SDD, para que o AIgnt-Synapse-Flow, a engine própria de pipeline do AIgnt OS, tenha um contrato uniforme ao chamar ferramentas externas.

Esta feature deve permanecer pequena: criar o adapter base, endurecer o contrato de resultado e tratar timeout/sanitização mínima sem antecipar adapters reais, pipeline, worker ou integrações mais pesadas.

# Objetivo

Entregar a base assíncrona de execução CLI com:
- contrato único de resultado para ferramentas externas;
- execução via `asyncio.create_subprocess_exec`;
- captura de `stdout` e `stderr`;
- timeout verificável com encerramento do processo;
- sanitização leve de streams para remover ANSI preservando o output bruto.

# Escopo

## Incluido

- `BaseCLIAdapter` assíncrono com método de comando para subclasses
- contrato tipado `CLIExecutionResult` evoluído para execução CLI real
- captura separada de `stdout_raw`, `stderr_raw`, `stdout_clean` e `stderr_clean`
- timeout controlado com término explícito do subprocesso
- sanitização leve e determinística de streams focada em remoção de ANSI e trim
- testes unitários com subprocesso falso e sem dependência de ferramenta real

## Fora de escopo

- adapters específicos de Codex, Gemini, Claude ou outras ferramentas
- parsing de fenced blocks, validação sintática de artefatos ou heurísticas por ferramenta
- retries, reroute, supervisor ou integração com AIgnt-Synapse-Flow além do contrato base
- execução prática em Docker ou validação operacional de container
- persistência, relatório de run ou worker residente

# Requisitos funcionais

1. O sistema deve oferecer um adapter base assíncrono para executar um comando CLI definido por subclass.
2. O adapter deve usar `asyncio.create_subprocess_exec`.
3. O adapter deve capturar `stdout` e `stderr` separadamente.
4. O adapter deve preservar os streams brutos recebidos do subprocesso.
5. O adapter deve expor versões limpas dos streams com remoção de ANSI.
6. O adapter deve calcular `duration_ms` para a execução.
7. O adapter deve considerar sucesso apenas quando não houver timeout e o retorno for zero.
8. O adapter deve sinalizar timeout de forma verificável e encerrar o processo antes de devolver o resultado.
9. O adapter não deve incorporar responsabilidades de parsing profundo já cobertas pela F04.

# Requisitos nao funcionais

- A implementacao deve continuar pequena e adequada a um recorte de 1 a 3 dias.
- Os testes devem ser deterministas e independentes de rede, Docker e ferramentas externas reais.
- A sanitização do adapter deve ser conservadora para não conflitar com o Parsing Engine MVP.
- O design deve permitir que adapters reais futuros herdem o contrato sem refatoração ampla.

# Casos de erro

- subprocesso retorna codigo de erro diferente de zero
- subprocesso excede timeout configurado
- streams contêm sequências ANSI misturadas a conteúdo semântico
- subclass devolve comando vazio ou inválido

# Cenarios verificaveis

## Cenario 1: execucao bem-sucedida

- Dado um adapter com comando válido
- Quando a execução termina com retorno zero
- Então o resultado contém tool_name, command, streams raw/clean, duration_ms e success verdadeiro

## Cenario 2: erro de retorno

- Dado um adapter cujo subprocesso termina com retorno diferente de zero
- Quando a execução termina sem timeout
- Então o resultado permanece estruturado
- E success fica falso

## Cenario 3: timeout verificável

- Dado um adapter cujo subprocesso excede o timeout configurado
- Quando a execução atinge o limite
- Então o processo é encerrado
- E o resultado marca timed_out como verdadeiro

## Cenario 4: sanitização conservadora

- Dado um output com sequências ANSI em stdout ou stderr
- Quando o adapter produzir o resultado
- Então os campos raw preservam o conteúdo original
- E os campos clean removem apenas ANSI e whitespace periférico

# Observacoes

Esta feature evolui `CLIExecutionResult` para o domínio do adapter e mantém o Parsing Engine da F04 separado. A sanitização do adapter fica deliberadamente mínima e não deve remover ruído operacional genérico; limpeza mais rica e extração de artefatos continuam pertencendo ao parser.
