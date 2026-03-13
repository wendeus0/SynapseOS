---
id: F42-tui-filters
type: feature
summary: "Filtros de visualização de steps no dashboard TUI para facilitar análise de runs longas ou com falhas."
inputs:
  - "Interação via teclado no dashboard TUI (aignt runs watch)"
outputs:
  - "Lista de steps filtrada na interface"
  - "Indicador visual do filtro ativo"
acceptance_criteria:
  - "O dashboard deve iniciar exibindo todos os steps (comportamento padrão)"
  - "Deve ser possível filtrar steps por estado 'failed' via tecla de atalho (ex: 'e')"
  - "Deve ser possível filtrar steps por estado 'running/pending' via tecla de atalho (ex: 'r')"
  - "Deve ser possível restaurar a visualização de todos os steps via tecla de atalho (ex: 'a')"
  - "A interface deve exibir claramente qual filtro está ativo no momento"
  - "A navegação (seleção de itens) deve se manter funcional após a aplicação do filtro"
non_goals:
  - "Busca textual livre (regex) nos logs ou nomes de steps"
  - "Persistência de filtros entre sessões do CLI"
  - "Combinação complexa de múltiplos filtros (AND/OR)"
---

# Contexto

O dashboard TUI (`aignt runs watch`) atualmente exibe uma lista linear de todos os steps executados em uma run. Em pipelines longos ou com muitas iterações (ex: loops de `worker`), essa lista pode crescer significativamente, dificultando a identificação rápida de falhas ou o acompanhamento dos steps ativos. A necessidade de "rolar" manualmente para encontrar erros é um ponto de atrito na UX, especialmente para triagem de falhas.

# Objetivo

Implementar um mecanismo de filtragem simples e rápido na lista de steps do dashboard TUI. O objetivo é permitir que o usuário alterne visualizações com teclas de atalho (mnemônicos) para focar no que importa no momento:
- **Erros**: Ver apenas o que falhou.
- **Atividade**: Ver apenas o que está rodando ou pendente.
- **Geral**: Ver o histórico completo.

A implementação deve ser puramente visual (client-side no TUI), sem alterar a persistência ou a lógica de execução.
