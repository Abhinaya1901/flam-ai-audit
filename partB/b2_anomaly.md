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
new completed tokens.

`reported_tok_s` counts total tokens processed — prompt tokens plus
generated tokens — divided by elapsed time, not just newly generated
tokens. Confirmed using the batch-24 row above (wall_clock_s = 61.16
from the raw log): 24 × (3584 + 512) / 61.16 = 1607.5, matching the
reported 1,607.4 almost exactly. If the column only counted generated
tokens, it would instead be 24 × 512 / 61.16 = 200.9 — far off from
what's reported. Preemption still lowers this number even though it's
the inflated metric, not the true generation rate: a preempted
sequence has to re-run prefill on resume, and that re-run consumes
wall-clock time without producing any tokens (prompt or generated) to
count toward the numerator, so the denominator grows faster than the
numerator and the ratio falls (7 preemptions at batch 32, 23 at batch 48).

## Proposed change

Cap scheduler batch size for long-prompt requests at 25 sequences (the
B1 capacity limit). Predicted effect: eliminates preemption-driven
rework, sustaining throughput near its observed peak (1,600 tok/s at
batch 24) instead of degrading to 1,300 tok/s at batch 48.

## Alternatives considered

Two other fixes are possible: (1) use a bigger GPU (more memory), so
more requests fit before running out of space, or (2) make each
token's saved data smaller (compression), so more requests fit in the
same memory. Not using these: (1) costs more money and doesn't fix the
actual scheduling problem, and (2) needs real engineering work and
could affect accuracy, which we haven't tested. The batch cap is
simplest and cheapest, and directly matches the number we already
calculated in B1.