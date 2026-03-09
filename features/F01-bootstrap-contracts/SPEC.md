---
id: F01-bootstrap-contracts
type: feature
summary: Estabelecer o bootstrap mínimo em Python do AIgnt OS com CLI básica, contratos iniciais, configuração base e testes iniciais.
workspace: .
inputs:
  - user_request
  - project_architecture_docs
outputs:
  - python_project_bootstrap
  - minimal_cli_entrypoint
  - initial_pydantic_contracts
  - base_configuration_model
  - initial_test_suite
constraints:
  - python-3.12+
  - typer
  - pydantic-v2
  - cli-first
  - spec-first
  - sem engine própria de pipeline nesta feature
  - sem worker nesta feature
  - sem parsing completo nesta feature
acceptance_criteria:
  - O projeto expõe uma CLI mínima executável que responde com help e versão sem depender de worker ou da engine própria de pipeline.
  - Existe um módulo de configuração base validado por Pydantic para defaults locais e overrides simples por ambiente.
  - Existem contratos/modelos iniciais explícitos e serializáveis para configuração da aplicação, solicitação básica de run e resultado básico de execução CLI.
  - Há testes automatizados iniciais cobrindo a subida da CLI, a validação da configuração base e a validação/serialização dos contratos iniciais.
  - A feature não introduz execução state-driven, worker residente, persistência SQLite nem parsing além do necessário para os contratos mínimos.
non_goals:
  - Implementar a engine própria de pipeline
  - Implementar worker residente
  - Implementar state machine
  - Implementar persistência de run
  - Implementar parsing robusto ou reparo de saída
  - Integrar ferramentas externas reais
security_notes:
  - Não usar shell=True no bootstrap de execução CLI
  - Não exigir segredos reais para subir a CLI mínima
---

## 1. Contexto

O projeto precisa de uma base mínima executável para começar o ciclo spec-first e TDD sem antecipar componentes maiores do MVP. Esta feature existe para criar um ponto de partida pequeno, verificável e coerente com a arquitetura definida para o AIgnt OS.

## 2. Objetivo

Entregar o menor bootstrap útil em Python para o AIgnt OS com:
- pacote Python inicial;
- CLI mínima funcional;
- contratos/modelos iniciais com Pydantic;
- configuração base validável;
- testes automatizados iniciais.

## 3. Escopo

Esta feature cobre apenas:
- estrutura mínima do pacote Python em `src/`;
- aplicação Typer com comando raiz e comando de versão, ou equivalente mínimo verificável;
- modelo de configuração base da aplicação;
- contratos Pydantic mínimos para dados de entrada e saída iniciais;
- suíte de testes inicial focada nesses contratos.

## 4. Fora de Escopo

Fica explicitamente fora desta feature:
- engine própria de pipeline;
- worker do runtime dual;
- execução de etapas `REQUEST -> COMPLETE`;
- adapters reais de ferramentas externas;
- parsing em camadas;
- geração de `RUN_REPORT.md`;
- observabilidade completa;
- persistência em SQLite ou filesystem operacional.

## 5. Regras Funcionais

1. O bootstrap deve usar Python 3.12+ como linguagem principal.
2. A CLI mínima deve ser baseada em Typer e iniciar sem depender de componentes ainda não implementados.
3. A CLI deve expor pelo menos uma forma verificável de inicialização bem-sucedida, com help e versão.
4. A configuração base deve ser representada por contrato explícito com validação.
5. Os contratos iniciais devem usar Pydantic v2 e manter baixo acoplamento.
6. Os contratos mínimos desta feature são:
   - configuração da aplicação;
   - solicitação básica de run;
   - resultado básico de execução CLI.
7. O contrato de resultado básico de execução CLI pode ser reduzido ao mínimo necessário nesta feature, desde que preserve a ideia de output bruto e output limpo como campos separados.
8. A feature deve deixar o projeto pronto para evolução posterior sem antecipar a engine própria de pipeline.

## 6. Casos de Erro

- A CLI deve falhar de forma clara quando a configuração base for inválida.
- O carregamento de configuração deve rejeitar valores incompatíveis com o schema.
- O contrato de solicitação básica de run deve rejeitar entrada vazia quando houver campo obrigatório de solicitação.
- O contrato de resultado básico de execução CLI deve rejeitar tipos inválidos nos campos estruturados.

## 7. Critérios de Aceite Detalhados

### AC1. CLI mínima
- Existe um entrypoint de CLI no pacote.
- Executar a CLI com help retorna sucesso.
- Executar a CLI para obter versão retorna sucesso.

### AC2. Configuração base
- Existe um modelo de configuração base com valores default explícitos.
- O modelo aceita override simples por ambiente ou mecanismo equivalente local.
- Configuração inválida gera erro de validação.

### AC3. Contratos iniciais
- Existem modelos Pydantic para configuração da aplicação, solicitação básica de run e resultado básico de execução CLI.
- Os modelos serializam para estruturas Python/JSON sem adaptação manual extra.
- Os modelos mantêm separação entre output bruto e output limpo quando aplicável.

### AC4. Testes iniciais
- Há testes automatizados para help da CLI.
- Há testes automatizados para versão da CLI.
- Há testes automatizados para defaults e erro de validação da configuração base.
- Há testes automatizados para validação e serialização dos contratos iniciais.

### AC5. Limite de escopo
- Nenhum teste desta feature depende de worker, state machine, pipeline, SQLite ou parsing avançado.
- Nenhum módulo desta feature implementa lógica de orquestração state-driven.

## 8. Artefatos Esperados

- `features/F01-bootstrap-contracts/SPEC.md`
- código inicial em `src/aignt_os/`
- testes iniciais em `tests/`
- `features/F01-bootstrap-contracts/NOTES.md` apenas se surgir lacuna relevante durante RED/GREEN

## 9. Observações para Planejamento

- Priorizar TDD explícito a partir dos critérios de aceite desta SPEC.
- Manter a implementação mínima e local.
- Evitar introduzir abstrações para pipeline, supervisor, worker ou persistência.
- Se houver dúvida sobre contratos futuros, escolher o menor shape compatível com a arquitetura e registrar a limitação em `NOTES.md`.

## 10. Observações para Revisão

- Confirmar que a feature continua pequena o suficiente para 1 a 3 dias.
- Confirmar que a terminologia usa “engine própria de pipeline”.
- Confirmar que a CLI sobe sem dependências de runtime ainda não implementado.
- Confirmar que os contratos permanecem explícitos e validados por Pydantic.
