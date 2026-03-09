# ADR-001 — Adotar orquestração via CLI em vez de orquestração baseada em API

## Status
Aceito

## Contexto
O AIgnt OS precisa integrar múltiplas ferramentas externas de IA com foco em eficiência de custo, flexibilidade operacional e execução local em Linux. Muitas das ferramentas-alvo já expõem CLIs utilizáveis e podem ser acessadas com menos atrito operacional do que integrações por API.

## Decisão
Usar orquestração via CLI, executando ferramentas externas por subprocess, como mecanismo principal de integração.

## Consequências
### Positivas
- menor custo operacional em cenários com assinatura fixa;
- modelo relativamente uniforme de integração;
- boa aderência ao ambiente local/Linux;
- menor dependência de SDKs e contratos proprietários.

### Negativas
- outputs ruidosos e pouco estruturados;
- maior complexidade de parsing;
- possibilidade de instabilidade entre versões de CLIs.

## Alternativas consideradas
- integração somente por APIs;
- integração híbrida API + CLI desde o início;
- wrappers baseados em browser automation.
