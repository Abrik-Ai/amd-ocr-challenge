# Experiment notes: OCR challenge

## Results (Qwen3-VL-8B-Instruct, bf16, Colab L4, prompt v1)

| set | images | score |
|---|---|---|
| samples, degraded x10 | 100 | 99/100 |
| synthetic clean (20 US, 10 CN, 16 signs) | 46 | 46/46 |
| synthetic degraded x10 | 460 | 454/460 (before CN fix: 451/460) |

- fix_cn_serial: Chinese plate serials never use I/O -> O to 0, I to 1 after the first two characters. Fixed 3 failures, broke none.
- Tried median filter + autocontrast: 98/100 vs 99/100 without; turned a correct 5 into S. Dropped.
- Remaining failures: province character on the strongest degradation (4), one 7/T, one US 0/O.