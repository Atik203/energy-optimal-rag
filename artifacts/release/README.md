# Sanitized per-query tables

These gzip CSVs let a reader rebuild the energy and accuracy tables without
redistributing SQuAD/HotpotQA text, gold answers, model predictions, or nonces.

Columns: `run_id`, `question_id`, `question_order`, `k`, `order_in_question`,
`correct_em`, `correct_lenient`, `f1`, `j_gpu_raw`, `j_gpu_calibrated`,
`j_retrieval_proxy`, `j_total`, `latency_s`, `prompt_tokens`, `output_tokens`,
`load_s`, `valid`, `invalid_reason`.

`question_id` is the upstream dataset identifier. No question, passage, gold
answer, or prediction text is included. Regenerate with
`python scripts/12_publish_runs.py`.
