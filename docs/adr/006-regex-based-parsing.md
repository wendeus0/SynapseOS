# ADR-006 — Adotar pipeline de parsing baseado em regex

## Status
Aceito

## Contexto
As ferramentas CLI geram outputs textuais ruidosos e o sistema precisa de limpeza e extração rápidas, controláveis e fáceis de ajustar incrementalmente.

## Decisão
Adotar parsing inicial baseado em regex, normalização textual e heurísticas leves, complementado por validação estrutural posterior.

## Consequências
### Positivas
- simples e rápido de implementar;
- eficaz para padrões conhecidos;
- fácil ajuste incremental por ferramenta.

### Negativas
- fragilidade diante de mudanças bruscas de output;
- necessidade de manutenção contínua;
- cobertura limitada para formatos altamente ambíguos.

## Alternativas consideradas
- exigir JSON estruturado de todas as ferramentas;
- parsing puramente baseado em LLM;
- parsers formais completos para cada ferramenta.
