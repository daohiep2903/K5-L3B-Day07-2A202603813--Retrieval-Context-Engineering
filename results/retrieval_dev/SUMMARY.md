# Retrieval dev results

Retrieval/context preparation only. No agent response, citation correctness or abstention has been evaluated. All runs use original questions, the same 116 chunks, and question-supplied filters.

| Config | Hit@1 | Hit@3 | Prepared-context evidence | Median ms |
|---|---:|---:|---:|---:|
| dense_baseline | 7/15 (46.7%) | 11/15 (73.3%) | 4/15 (26.7%) | 36.11 |
| lexical_baseline | 9/15 (60.0%) | 13/15 (86.7%) | 6/15 (40.0%) | 1.30 |
| hybrid_baseline | 10/15 (66.7%) | 14/15 (93.3%) | 5/15 (33.3%) | 32.51 |
| dense_context_3000 | 7/15 (46.7%) | 11/15 (73.3%) | 11/15 (73.3%) | 31.33 |
| hybrid_top6_context_3000 | 10/15 (66.7%) | 14/15 (93.3%) | 14/15 (93.3%) | 27.79 |

No-evidence questions: two dev cases per configuration have traces but are excluded from these three metric denominators. No abstention score is inferred from retrieval.

Provisional retrieval candidate: hybrid_top6_context_3000. This is not the final agent configuration; compare real agent responses and costs on dev before freezing test settings.

Initialization was measured separately. Search timings are one sequential pass per config with warm/cache effects, not a controlled speed ranking. Paid API service cost is zero; hardware/network costs were not measured.

See docs/RETRIEVAL_DEV.md for Vietnamese interpretation and dev failure examples.
