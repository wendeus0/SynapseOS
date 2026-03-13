---
id: F39-dashboard-logs
type: feature
summary: "Visualização de logs (stdout/stderr) no TUI Dashboard"
inputs:
  - "Tecla Enter na lista de steps"
outputs:
  - "Modal com conteúdo do log (clean ou raw)"
acceptance_criteria:
  - "Deve abrir modal ao pressionar Enter em um step"
  - "Deve exibir conteúdo de clean_output_path se existir"
  - "Deve fazer fallback para raw_output_path se clean não existir"
  - "Deve exibir mensagem de erro se arquivo não for encontrado"
  - "Deve permitir fechar o modal com ESC"
non_goals:
  - "Streaming de logs em tempo real (apenas snapshot)"
  - "Edição de logs"
  - "Busca textual dentro do modal"
---

## Contexto

O dashboard TUI (F33) permite monitorar o estado dos steps, mas não o conteúdo gerado por eles. Para debug e acompanhamento, é essencial visualizar o `stdout` e `stderr` de cada execução sem sair da interface.

Esta feature (originalmente implementada como parte do ciclo da F33/F34) foi regularizada como F39 para evitar colisão de ID com a feature de ownership (F34).

## Objetivo

Implementar um `LogViewer` modal que exibe o conteúdo dos arquivos de log persistidos pelo runtime, permitindo inspeção rápida do resultado de cada ferramenta.
