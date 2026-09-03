# B2 — Throughput Anomaly at High Batch Size

## The anomaly

From `bench_log.csv`, `prompt_len=3584, gen_len=512` rows:

| batch | reported_tok_s | preempted_seqs | kv_cache_util |
|---|---|---|---|
| 4  | 565.4  | 0  | 0.16 |
| 8  | 902.6  | 0  | 0.31 |
| 16 | 1,311.4 | 0  | 0.62 |
| 24 | 1,607.4 | 0  | 0.93 |
| 32 | 1,384.0 | 7  | 0.97 |
| 48 | 1,298.5 | 23 | 0.97 |

Throughput peaks at batch 24 (1,607.4 tok/s) and **falls** at batch 32
and 48, despite more requests running — contradicting the naive
"throughput scales with batch" assumption.

## Mechanism

Batch 24 sits at ~93% KV cache utilization with zero preemptions —
right at the GPU's real capacity (25-26 sequences, per B1). Pushing
batch size past that (32, 48) forces the scheduler to preempt sequences
(evict and later resume them), since there isn't enough memory to hold
them all. Preempted sequences must recompute work already done before
eviction — wasted computation that consumes real time but produces no
new completed tokens. Since `reported_tok_s` = tokens completed ÷
elapsed time, this wasted rework directly lowers the measured
throughput as batch size grows past capacity (7 preemptions at batch
32, 23 at batch 48).

## Proposed change

Cap scheduler batch size for long-prompt requests at 25 sequences
(the B1 capacity limit). Predicted effect: eliminates preemption-driven
rework, sustaining throughput near its observed peak (1,600 tok/s at
batch 24) instead of degrading to 1,300 tok/s at batch 48.