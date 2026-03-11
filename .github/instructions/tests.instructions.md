---
applyTo: "tests/**/*.py"
---

# Testes — Instruções de contexto

## Execução

```bash
# Suite completa
uv run --no-sync python -m pytest

# Arquivo específico
uv run --no-sync python -m pytest tests/unit/test_state_machine.py

# Teste específico
uv run --no-sync python -m pytest tests/unit/test_state_machine.py::test_state_machine_follows_minimal_happy_path_to_complete
```

Use sempre `python -m pytest` — o wrapper bare pode falhar neste repositório.

## Estrutura de diretórios

```
tests/
  unit/          # testes de unidade: módulos isolados, sem I/O real
  integration/   # testes de integração: CLI bootstrap, runtime lifecycle
  fixtures/
    specs/       # fixtures de SPEC válidas e inválidas para o SpecValidator
  pipeline/      # reservado — sem cobertura real ainda
```

Não misture testes de unidade e integração no mesmo arquivo.

## Nomeação

- Arquivos: `test_<módulo>.py` — espelhando o caminho do módulo testado.
- Funções: `test_<o_que_faz>_<cenário>` — descreva comportamento, não implementação.
- Exemplo: `test_state_machine_blocks_plan_before_spec_validation`

## Fixtures

- Fixtures de escopo de session/module em `conftest.py` no nível adequado.
- Fixtures de escopo de função diretamente no arquivo de teste quando usadas uma vez.
- Prefira factories simples a mocks complexos.

## O que testar

- Comportamento observável externamente — o que o módulo faz, não como faz.
- Casos felizes e casos de erro esperados (incluindo exceções customizadas do projeto).
- Contratos: se a SPEC define `acceptance_criteria`, escreva testes que verifiquem exatamente esses critérios.

## O que evitar

- Não mocke o que pode ser testado com a implementação real (ex: não mocke o `SpecValidator`).
- Não teste detalhes de implementação interna (atributos privados, métodos internos).
- Não escreva testes que passam trivialmente sem validar comportamento real.
- Não use `time.sleep` em testes — use mocks de tempo quando necessário.

## Cobertura

- Não existe um percentual mínimo obrigatório, mas todo código novo deve ter pelo menos um teste cobrindo o caminho principal.
- SPECs têm `acceptance_criteria` — cada critério deve ter pelo menos um teste correspondente.

## Exceções do projeto

- `InvalidStateTransition` (state_machine): teste cenários de transição inválida explicitamente.
- `SpecValidationError` (spec validator): teste com fixtures de SPEC inválida já existentes.
- `RuntimeInconsistentError`: teste via CLI integration, não diretamente no serviço.
