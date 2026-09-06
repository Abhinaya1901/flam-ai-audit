# B3 — The "one column" misread

## What reported_tok_s is actually counting

REPORT_v0 treats `reported_tok_s` as if it only measures new words the
model writes (decode speed). It doesn't. As we found in B2,
`reported_tok_s` = (prompt words + generated words) × number of
requests ÷ time taken. It counts the words the model had to read
(the prompt) the same as the words it actually produced.

## Honest goodput for the batch-24 long-prompt row (worked out two ways)

Row we're using: prompt=3584 words, generated=512 words, 24 requests,
took 61.16 seconds, reported_tok_s=1607.4

**Way 1 — just count the real output directly, ignore reported_tok_s
completely:**
512 words generated × 24 requests ÷ 61.16 seconds ≈ 200.9 tok/s

**Way 2 — work backwards from reported_tok_s once we know what it's
made of:**
Out of every 4096 words counted (3584 prompt + 512 generated), only
512 were actually new output — that's 1/8 of the total. So:
1607.4 × (1/8) ≈ 200.9 tok/s

Both ways land on the same number, ~201 tok/s. That's about 8x lower
than the 1607 headline number — because 7 out of every 8 "words"
counted were just the prompt being read, not new content being
produced.

## Why this one mistake caused both of REPORT_v0's wrong conclusions

**"Longer prompts give better throughput"** — not true once you count
fairly. Short-prompt requests at batch 16 actually produce real output
faster: 256 words × 16 requests ÷ 13.91 seconds ≈ 294.5 tok/s. That's
higher than the long-prompt batch 24 result of ~201 tok/s. Long
prompts only looked faster because reading a big prompt got counted as
if it were the same as writing new words.

**"Batch 48 will give ~3200 tok/s"** — this was guessed by just
doubling the 1607.4 number, assuming that doubling the batch size
doubles the speed. But the log itself shows that's wrong: at batch 32
and 48, the reported number actually goes down (1384.0, then 1298.5),
because of the preemption problem explained in B2. Working out the
real output speed at batch 48: 1298.5 × (1/8) ≈ 162 tok/s — lower than
batch 24, nowhere close to the claimed 3200.

## What the report should have said instead

The real speed at which the model actually produces new content peaks
around batch 24, at about 201 tok/s — not 1607. Long prompts are
actually slower for real output than short prompts, not faster. And
speed doesn't keep climbing with batch size — past around batch 25, it
gets worse, because the GPU runs out of memory and starts having to
redo work (see B2). Any capacity planning should use this real output
speed, not the raw counter, and should treat ~25 sequences as a hard
limit, not a starting point to scale up from.

---

# B4 — How we'd confirm the B2 explanation in a real live system

The column names already in this log (`preempted_seqs`,
`kv_cache_util`) look like the kind of internal stats a serving system
like vLLM tracks live. So in a real production setup, we'd want to
watch that same kind of live counter — something that tracks how many
times the system has had to kick out and later resume a request. We'd
expect that counter to stay at basically zero while memory usage is
under about 93%, matching what happened at batch 24 and below in our
log, and then jump up sharply once memory usage crosses roughly
95-97% — the same pattern we already see in the log (7 kick-outs at
batch 32, 23 at batch 48). A second thing worth watching: how long it
takes to get the first word back for requests that got kicked out —
since a kicked-out request has to re-read its prompt from scratch when
it resumes, that wasted re-reading should show up as extra delay
specifically for those requests, not just as a general slowdown across
the board.
