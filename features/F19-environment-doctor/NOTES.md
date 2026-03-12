# F19 Notes

- A F19 adota `aignt doctor` como superficie publica principal, em vez de `aignt runtime doctor`, porque o recorte e diagnosticar o ambiente do fluxo publico atual e nao apenas o lifecycle do runtime.
- O doctor da F19 continua propositalmente local: sem Docker, sem credenciais externas, sem MCP e sem auto-fix.
- Runtime parado continua sendo `warn`, nao `fail`, porque o caminho canonico atual da etapa 2 permanece sincrono e nao exige worker residente para a primeira demonstracao oficial.
- Se surgir necessidade real de validar Docker/container como pre-requisito do fluxo minimo, isso deve acionar `repo-preflight` e possivelmente revisar a SPEC da F19, em vez de ampliar esta frente silenciosamente.
