# Agent dev: measured comparison

All dev labels below were approved by the student on 2026-11-15. Review methodology and initial records are retained in student_dev_review_confirmation.json and review_history/. Original raw model calls, refusals and source mappings are retained. No test execution.

| Config | Answer 0/1/2 | Mean /2 | Supported citations | Correct abstention | False abstention | Final-context evidence | Cost estimate USD |
|---|---|---:|---:|---:|---:|---:|---:|
| dense_baseline | 14/1/0 | 0.067 | 0/2 | 2/2 | 13/15 | 5/15 | 0.008587 |
| lexical_baseline | 14/1/0 | 0.067 | 0/1 | 2/2 | 14/15 | 6/15 | 0.008995 |
| hybrid_baseline | 15/0/0 | 0.000 | 0/1 | 2/2 | 14/15 | 6/15 | 0.008856 |
| dense_context_3000 | 14/0/1 | 0.133 | 2/2 | 2/2 | 14/15 | 12/15 | 0.010201 |
| hybrid_top6_context_3000 | 11/1/3 | 0.467 | 4/4 | 2/2 | 11/15 | 13/15 | 0.011336 |
| hybrid_top6_context_3000_formatted | 1/2/12 | 1.733 | 15/17 | 2/2 | 0/15 | 13/15 | 0.011408 |

Total: 102 real dev traces; estimated API cost $0.059383 (no cache discount).

Selected on dev: hybrid_top6_context_3000_formatted. See results/dev_selection.json.

Citation formatter only renders model-declared IDs verified in context; it does not create evidence or semantically verify claims. The first five configurations are unchanged original runs. The formatted configuration is an additional real 17-case run after dev error analysis, not an offline replacement of failed outputs.

See docs/AGENT_DEV.md for Vietnamese methods, remaining errors and limitations.
