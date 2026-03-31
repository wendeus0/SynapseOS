---
feature_id: F57
feature_name: Security Gate Tests
status: draft
author: opencode
created: 2026-03-31
---

# F57 — Security Gate Tests

## Objetivo

Criar suíte de testes dedicada para o módulo de segurança (`src/synapse_os/security.py`), cobrindo sanitização de texto, detecção de segredos, validação de paths e computação de hashes. O módulo já existe com funções de sanitização mas não possui testes unitários dedicados — apenas testes indiretos em `test_runtime_service_security.py`.

## Por que isso importa

O módulo de segurança é o gate de proteção contra vazamento de segredos, path traversal e injeção de caracteres maliciosos. Sem testes dedicados:

- Padrões de segredos podem falhar silenciosamente
- Path traversal pode não ser detectado em edge cases
- Sanitização de texto pode regressar sem aviso

## Escopo

### Incluído

- Testes unitários para `normalize_unicode`
- Testes unitários para `strip_bidi_controls`
- Testes unitários para `strip_ansi_sequences`
- Testes unitários para `mask_secrets` com padrões default e custom
- Testes unitários para `sanitize_clean_text` com combinações de flags
- Testes unitários para `resolve_path_within_root` com paths válidos e traversal
- Testes unitários para `compute_file_sha256`
- Testes de integração com o security-gate.sh script

### Não incluído

- Testes do `security-gate.sh` script (já cobertos em `test_repo_automation.py`)
- Testes de performance de hashing em arquivos grandes

## Critérios de Aceite

- [ ] AC1: `test_normalize_unicode_converts_nfkc` — normaliza Unicode para NFKC
- [ ] AC2: `test_strip_bidi_controls_removes_directional_chars` — remove controles bidirecionais
- [ ] AC3: `test_strip_ansi_sequences_removes_color_codes` — remove sequências ANSI
- [ ] AC4: `test_mask_secrets_hides_github_tokens` — mascara tokens GitHub (ghp*, ghs*)
- [ ] AC5: `test_mask_secrets_hides_bearer_tokens` — mascara Bearer tokens
- [ ] AC6: `test_mask_secrets_hides_openai_keys` — mascara chaves sk-\*
- [ ] AC7: `test_mask_secrets_custom_patterns` — aplica padrões customizados
- [ ] AC8: `test_sanitize_clean_text_combines_all_sanitizers` — combina todos os sanitizers
- [ ] AC9: `test_resolve_path_within_root_accepts_valid_path` — aceita path dentro do root
- [ ] AC10: `test_resolve_path_within_root_rejects_traversal` — rejeita path traversal (../)
- [ ] AC11: `test_compute_file_sha256_returns_correct_hash` — hash SHA256 correto para conteúdo conhecido
- [ ] AC12: `test_security_gate_accepts_current_operational_surface` — script security-gate.sh passa

## Design de Testes

### Fixtures

- Texto com caracteres Unicode mistos (NFC, NFD, NFKC)
- Texto com controles bidirecionais (\u202E, \u200E, etc.)
- Texto com sequências ANSI coloridas
- Texto com segredos embutidos (ghp_xxx, Bearer xxx, sk-xxx)
- Paths válidos e maliciosos para path traversal

## Dependências

- `src/synapse_os/security.py` — módulo alvo
- `scripts/security-gate.sh` — script de validação
