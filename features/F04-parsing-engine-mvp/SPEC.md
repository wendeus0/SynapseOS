---
id: F04-parsing-engine-mvp
type: feature
summary: Implementar o Parsing Engine MVP para limpar outputs ruidosos, extrair blocos relevantes e validar artefatos basicos antes dos hand-offs da pipeline.
workspace: .
inputs:
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/adr/006-regex-based-parsing.md
  - cli_execution_results_or_equivalent_raw_outputs
outputs:
  - parsing_contracts
  - text_normalization_and_cleaning
  - fenced_block_extractors
  - basic_artifact_validators
  - parsing_fixtures_and_tests
constraints:
  - manter escopo estritamente no parsing de outputs textuais
  - nao implementar adapter async, subprocess orchestration ou roteamento
  - nao acoplar a feature a uma ferramenta externa especifica
  - preservar a separacao entre output bruto e output limpo
  - seguir heuristicas leves com regex e validacao estrutural posterior
acceptance_criteria:
  - Existe limpeza automatizada de saida textual para remover sequencias ANSI e ruido operacional basico sem destruir blocos uteis.
  - Existe extracao automatizada de ao menos blocos fenced de Markdown relevantes para hand-off basico.
  - Existe validacao automatizada para aceitar bloco Python sintaticamente valido e rejeitar bloco Python corrompido.
  - O resultado do parsing expoe dados estruturados consumiveis sem substituir o output bruto original.
  - Os testes cobrem output com ANSI, extracao de bloco Python e falha verificavel para artefato corrompido.
non_goals:
  - implementar adapter base async
  - chamar subprocessos reais
  - suportar parsing especifico por ferramenta real
  - reparar automaticamente artefatos corrompidos com LLM
  - integrar pipeline completa, worker ou persistencia
dependencies:
  - F03-state-machine-mvp
---

# Contexto

O AIgnt OS trata parsing como preocupacao arquitetural central porque as ferramentas CLI produzem saidas textuais ruidosas, misturando texto util, ruido operacional, codigos ANSI e blocos de artefatos. Depois da F02 e da F03, o proximo incremento natural do nucleo e criar o primeiro Parsing Engine executavel para preparar hand-offs confiaveis no AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS.

O recorte desta feature precisa permanecer pequeno: limpar texto, extrair blocos relevantes e validar artefatos basicos sem antecipar adapter async, supervisor, reroute ou suporte detalhado por ferramenta.

# Objetivo

Entregar o Parsing Engine MVP com:
- normalizacao textual minima;
- limpeza de ruido e sequencias ANSI;
- extracao de blocos fenced relevantes;
- validacao basica de artefatos extraidos;
- testes automatizados com fixtures de outputs ruidosos.

# Escopo

## Incluido

- limpeza textual deterministica de outputs com ANSI e ruido operacional comum
- extracao de blocos fenced Markdown com preservacao do conteudo interno
- suporte minimo para identificar linguagem declarada no fence quando presente
- validacao estrutural minima para artefatos extraidos
- validacao sintatica de bloco Python via `ast.parse()` ou mecanismo equivalente
- contratos tipados para representar resultado do parsing
- fixtures e testes unitarios focados em cleaner, extractor e validator

## Fora de escopo

- parsing especifico por ferramenta real
- chamadas de subprocesso
- timeout, retries ou politicas de execucao
- reparo automatico de artefato invalido
- parsing profundo de JSON/YAML arbitrario fora do necessario para este recorte
- integracao com pipeline manager, supervisor, worker ou memoria

# Requisitos funcionais

1. O sistema deve aceitar input textual bruto e produzir um resultado estruturado de parsing.
2. O sistema deve preservar o output bruto recebido sem mutacao destrutiva.
3. O sistema deve produzir uma versao limpa do texto com remocao de sequencias ANSI.
4. O sistema deve remover ruido operacional basico quando isso nao destruir blocos fenced ou conteudo relevante.
5. O sistema deve extrair blocos fenced Markdown presentes no texto limpo.
6. O sistema deve expor ao menos o conteudo do bloco e a linguagem declarada quando houver.
7. O sistema deve oferecer validacao minima para blocos Python extraidos.
8. O sistema deve falhar de forma verificavel quando um artefato Python extraido estiver corrompido.
9. O sistema nao deve depender de LLM nem de parser especifico por fornecedor para cumprir esta feature.

# Requisitos nao funcionais

- A implementacao deve permanecer pequena o suficiente para 1 a 3 dias.
- O parsing inicial deve seguir a decisao de regex, normalizacao textual e heuristicas leves definida no ADR-006.
- O design deve continuar compativel com evolucao futura para parsers por ferramenta sem exigir reescrita total do recorte atual.
- Os testes devem ser deterministas e independentes de rede, Docker ou ferramentas externas reais.

# Casos de erro

- output contendo sequencias ANSI e ruido misturado a texto util
- texto sem blocos fenced relevantes
- bloco fenced com linguagem Python e codigo sintaticamente invalido
- fences malformados que inviabilizem extracao confiavel
- output ruidoso em que o cleaner nao pode simplesmente apagar tudo sem perder artefato relevante

# Cenarios verificaveis

## Cenario 1: limpeza de output ruidoso

- Dado um output textual com codigos ANSI e ruido operacional basico
- Quando o cleaner for executado
- Entao o resultado limpo remove o ruido previsto pelo recorte
- E preserva o conteudo util necessario para extracao posterior

## Cenario 2: extracao de bloco Python

- Dado um output limpo contendo um bloco fenced Markdown com linguagem `python`
- Quando o extractor for executado
- Entao o bloco e retornado como artefato estruturado
- E a linguagem declarada fica acessivel para validacao posterior

## Cenario 3: validacao de bloco Python valido

- Dado um bloco Python extraido com sintaxe valida
- Quando o validator for executado
- Entao a validacao passa sem erro

## Cenario 4: rejeicao de bloco corrompido

- Dado um bloco Python extraido com sintaxe invalida ou fence corrompido
- Quando o validator for executado
- Entao a falha e explicita e verificavel por teste

# Observacoes

Esta feature nao deve expandir `CLIExecutionResult` para cobrir subprocesso, timeout ou stderr adicionais; isso pertence a F05. Se surgir necessidade de contrato novo, ele deve ser restrito ao dominio de parsing e manter a separacao entre output bruto, output limpo e artefatos extraidos.
