# Agent test results

Frozen baseline and selected configuration, seven cases each. No model/prompt/retrieval tuning after seeing test results. Student approved all test reviews on 2026-11-15; original method/history retained in results/student_test_review_confirmation.json and results/review_history/.

| Configuration | Original Hit@1 | Original Hit@3 | Context evidence | Answer 0/1/2 | Mean /2 | Supported citations | Correct refusal | False refusal |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| dense_baseline | 4/5 | 5/5 | 3/5 | 5/0/0 | 0.0 | 0/0 | 2/2 | 5/5 |
| hybrid_top6_context_3000_formatted | 4/5 | 5/5 | 5/5 | 0/2/3 | 1.6 | 5/7 | 2/2 | 0/5 |

Baseline citation validity 0/0 is not applicable; it returned no answers/citations. Its correct refusal 2/2 must be read with false refusals 5/5: refusing everything is not evidence of a strong abstention policy.

Estimated API total $0.008476; no cache discount, no local-compute cost; not billing invoice.

Selected test-01 has the correct scope answer but wrong/insufficient citation C002 rather than C041. Selected test-04 includes an unsupported CSRF rationale and cites an implicit-error-flow excerpt for authorization-code scope. No changes are made to improve these test outcomes.

See docs/AGENT_TEST.md and review packet for Vietnamese explanations.
