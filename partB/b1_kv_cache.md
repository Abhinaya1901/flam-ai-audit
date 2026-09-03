# B1 — KV-cache Math

**Unit convention:** all memory figures use decimal GB (1 GB =
1,000,000,000 bytes), matching how `model_spec.md` states GPU memory
capacity (hardware memory specs are conventionally decimal, unlike
software-reported allocations which often use binary GiB).

## (a) Bytes of KV cache per token

Per layer, the model stores a Key and a Value, each sized (KV heads ×
head_dim), in fp16 (2 bytes per number):
2 (K and V) × 8 (KV heads) × 128 (head_dim) × 2 bytes = 4,096 bytes/token/layer


Across all 28 layers:
4,096 bytes × 28 layers = 114,688 bytes per token


**One token costs exactly 114,688 bytes of KV cache.**

## (b) Maximum concurrent 4096-token sequences

### GPU capacity available for KV cache

Total GPU memory:
24 GB = 24,000,000,000 bytes

After 92% utilization:
24,000,000,000 × 0.92 = 22,080,000,000 bytes

Model weights:
4.2B params × 2 bytes = 8,400,000,000 bytes

Subtract model weights:
22,080,000,000 − 8,400,000,000 = 13,680,000,000 bytes

Overhead:
1.6 GB = 1,600,000,000 bytes

Subtract overhead:
13,680,000,000 − 1,600,000,000 = 12,080,000,000 bytes

**Result: 12,080,000,000 bytes available for KV cache**


#Note: a naive calculation that skips subtracting the model's own
weights would estimate ~43-47 sequences. This does not match the log's
implied capacity (25.8), which shows why model weights
must be subtracted they occupy a large, fixed share of GPU memory
before any KV cache can be allocated.

### Converting to sequence capacity
Max tokens: 12,080,000,000 ÷ 114,688 ≈ 105,300 tokens
Max 4096-token sequences: 105,300 ÷ 4096 ≈ 25.7


**Predicted capacity: ~25-26 concurrent full-length (4096-token) sequences.**

## Checking the prediction against the log

From `bench_log.csv`, filtering to `prompt_len=3584` + `gen_len=512`
(total = 4096, the full context window), the log's `kv_cache_util`
column shows what fraction of KV cache capacity was in use at each
batch size. Dividing batch size by utilization gives the implied total
capacity:

| batch | kv_cache_util | implied capacity (batch ÷ util) |
|---|---|---|
| 4  | 0.16 | 25.0 |
| 8  | 0.31 | 25.8 |
| 16 | 0.62 | 25.8 |
| 24 | 0.93 | 25.8 |

The log consistently implies a true capacity of ~25.8 sequences across
four independent rows.

## Conclusion

The corrected calculation (25.7) matches the log's implied capacity
(~25.8) almost exactly. This confirms both the arithmetic and the
choice of decimal GB as the correct unit convention using binary
GiB instead would have predicted 28.9, a noticeably worse match to
the real data. The key lesson from the first (wrong) attempt: any GPU
capacity calculation must account for the model's own weights
occupying memory, not just the stated utilization cap and overhead.