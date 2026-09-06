# B1 — KV-cache Math

**Unit convention:** decimal GB (1 GB = 1,000,000,000 bytes), matching
`model_spec.md`'s convention for GPU memory capacity.

## (a) Bytes of KV cache per token

Per layer: 2 (K+V) × 8 (KV heads) × 128 (head_dim) × 2 bytes (fp16) =
4,096 bytes/token/layer. Across 28 layers: 4,096 × 28 = **114,688
bytes per token**.

## (b) Maximum concurrent 4096-token sequences

| step | bytes |
|---|---|
| Total GPU memory | 24,000,000,000 |
| × 92% utilization | 22,080,000,000 |
| − model weights (4.2B × 2 bytes) | 13,680,000,000 |
| − overhead (1.6GB) | **12,080,000,000 available for KV cache** |

Max tokens: 12,080,000,000 ÷ 114,688 ≈ 105,300. Max 4096-token
sequences: 105,300 ÷ 4096 ≈ **25.7**.

Note: skipping the model-weights subtraction gives ~43-47 sequences
instead — a naive mistake that doesn't hold up against the log below,
since it ignores that weights occupy a large fixed share of memory
before any KV cache can be allocated.

## Checking against the log

`bench_log.csv`, filtering to prompt_len=3584 + gen_len=512 (=4096,
full context). Dividing batch size by `kv_cache_util` gives implied
total capacity:

| batch | kv_cache_util | implied capacity (batch ÷ util) |
|---|---|---|
| 4  | 0.16 | 25.0 |
| 8  | 0.31 | 25.8 |
| 16 | 0.62 | 25.8 |
| 24 | 0.93 | 25.8 |

Consistent ~25.8 across four independent rows.

## Conclusion

25.7 (calculated) vs. 25.8 (log-implied) — a near-exact match, and
confirms decimal GB as the right unit convention (binary GiB would
predict 28.9, a worse fit). Any GPU capacity calculation must subtract
the model's own weights, not just the utilization cap and overhead.