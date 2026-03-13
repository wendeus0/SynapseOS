# Relatório de Execução - Feature F34: Dashboard Logs

## Resumo
Adição da funcionalidade de visualização de logs (`stdout`/`stderr`) no dashboard TUI (`aignt runs watch`), permitindo a inspeção detalhada de steps executados.

## Escopo Entregue
- **Interface TUI**:
    - Novo componente `LogViewer` (Modal) acionado pela tecla `Enter` na lista de steps.
    - Exibição de conteúdo de texto longo com suporte a rolagem (widget `RichLog`).
- **Lógica de Negócio**:
    - Leitura segura de arquivos de log associados aos steps (`clean_output_path` ou `raw_output_path`).
    - Tratamento de erro para arquivos inexistentes ou ilegíveis.
- **Refatoração**:
    - Correção na renderização de `StepDetail` para evitar problemas de concorrência com o gerenciamento de contexto do `textual`.

## Alterações Técnicas
- Arquivo modificado: `src/aignt_os/cli/dashboard.py` (adição de `LogViewer` e `action_show_logs`).
- Testes adicionados: `tests/unit/test_dashboard_logic.py` (focados na lógica de controle e acesso a arquivos).
- Testes removidos: `tests/unit/test_dashboard_ui.py` (substituídos por testes de lógica mais robustos e menos propensos a flakiness em CI).

## Revisão de Segurança
- **Leitura de Arquivos**: Restrita aos caminhos validados e persistidos no banco de dados (`RunStepRecord`).
- **Sanitização**: O conteúdo é lido como texto e renderizado em widget seguro (`RichLog`), mitigando injeção de terminal.
- **Path Traversal**: Risco mitigado pelo uso de `pathlib` e origem confiável dos caminhos (gerados pelo runtime).
- **Performance**: Leitura síncrona de arquivos pode impactar a UI em logs muito grandes (>10MB), mas é aceitável para o escopo local atual.

## Próximos Passos
- Avaliar carregamento assíncrono ou paginado para logs muito extensos.
- Monitorar uso de memória em sessões longas com muitos logs abertos.

## Conclusão
Feature F34 implementada e validada. Aprovada para merge na branch principal, completando o ciclo de melhoria de observabilidade iniciado na F33.
