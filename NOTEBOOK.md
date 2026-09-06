# Audit Notebook — Tokenizer & Serving Report

## A1 — Eval Corpus

**Source:** FLORES-200, obtained via the `Muennighoff/flores200` mirror
on Hugging Face. The canonical `openlanguagedata/flores_plus` repo is
gated and requires HuggingFace account authentication, so this public
mirror was used instead (required downgrading the `datasets` library to
2.19.0, since this mirror uses an older loading-script format the
newest library version no longer supports).

**Languages:** English (eng_Latn), Hindi (hin_Deva), Tamil (tam_Taml),
Telugu (tel_Telu).

**Size:** `dev` split = 997 sentences per language, `devtest` split =
1012 sentences per language. `dev` used for exploratory analysis while
building/testing the corrected script; `devtest` reserved for final
reported numbers in A3/A4.

**Domain:** English source sentences were sampled in equal thirds from
Wikinews (international news), Wikijunior (non-fiction children's
books), and Wikivoyage (travel guides), covering topics like politics,
science, health, crime, and travel. Average sentence length ~21 words.
This is formal, edited, encyclopedic/journalistic prose — not
conversational text.

**Preprocessing:** none applied at download — sentences used exactly as
provided.

**Verification:** manually inspected the first 3 lines across all 4
language files and confirmed they are genuinely parallel — same source
sentence/topic per line, same order, across all languages (e.g. line 1
in every file covers the same Stanford diagnostic-chip story).

**What this corpus cannot tell us:** it is formal, edited, multi-domain
written prose, not casual conversational text — which is what a
production chatbot actually processes. Fertility numbers measured here
may not transfer to shorter, informal, or code-mixed text real users
type (e.g. Hindi written in Latin script, "Hinglish"), which is common
in real traffic but entirely absent from FLORES. Also, ~1000 sentences
per language, while far larger than the original 10-line toy sample, is
still a modest size — rare tokenization edge cases (unusual proper
nouns, numerals, domain jargon) may be underrepresented. Any production
recommendation from this corpus should be validated against real
traffic before being finalized.

---

## A2 — Script/Metric Audit (fertility.py)

**Baseline reproduced.** Ran the original script exactly as given on
the toy corpus (`eng_sample.txt`, `hin_sample.txt`). Output matched
REPORT_v0.md exactly: eng=1.27, hin=7.45, ratio=5.89x. Confirms the
report's numbers are reproducible from the script as-is.

### Bug 1 — double space inflates word count
`eng_sample.txt` line 7 has a double space ("...the books  in the
cupboard."). Tested `line.split(" ")` directly: produces
`['...', 'books', '', 'in', ...]` — the double space creates a fake
empty-string "word," inflating `len(words)` from 7 to 8. Since fertility
divides tokens by `len(words)`, this understates fertility on affected
lines. Confirmed the same issue exists in `hin_sample.txt` line 10.

Isolated the fix (`split(" ")` → `split()`) and measured:
- Toy corpus: eng=1.27→1.28, hin=7.45→7.60, ratio 5.89x→5.92x
- Real FLORES corpus (997 lines): ratio 6.093x→6.094x — even smaller
  effect than on the toy corpus, contradicting my initial guess that
  more lines would mean a bigger effect.

**Verdict:** real, confirmed bug — but negligible impact at any scale
tested.

### Bug 2 — `.lower()` understates the true Hindi/English gap
Removed `line = line.lower()` and measured:
- Toy corpus: eng=1.27→1.23, hin unchanged (7.45), ratio 5.89x→6.06x
- Real FLORES corpus: ratio 6.093x→6.318x — effect held and slightly
  strengthened at scale

Hindi is completely unaffected by removing `.lower()` since Devanagari
has no uppercase/lowercase distinction, which confirms the mechanism.
English fertility drops without lowercasing because capitalized words
like "NASA" and "GPU" are more likely to be recognized as single GPT-2
tokens. The ratio gets **worse**, not better, meaning the original
report's `.lower()` step was understating the true gap, not the other
way around.

**Verdict:** real, robust, materially important — strong finding.

### Bug 3 — `chars = len(line)` counts codepoints, not real characters
`len(line)` counts Unicode codepoints. Devanagari, Tamil, and Telugu all
combine a base consonant with a separate vowel-sign codepoint to form
one visual character (grapheme) — so `len()` overcounts "characters" for
these scripts. Tested using the `grapheme` library on the real FLORES
`dev` corpus, comparing codepoint count vs. true grapheme count:

| language | codepoints | graphemes | ratio |
|---|---|---|---|
| English (control) | 125,194 | 125,194 | 1.000 |
| Hindi | 125,366 | 87,046 | 1.440 |
| Tamil | 146,128 | 94,467 | 1.547 |
| Telugu | 127,176 | 81,234 | 1.566 |

English's ratio of exactly 1.000 confirms this is a script-specific
encoding artifact, not a general issue. All three Indian scripts
overcount substantially, and the degree varies unpredictably between
them (Telugu is worst, not Hindi).

Recomputing with true graphemes: reported hin tok/char of 1.579
corresponds to a true tok/grapheme of ~2.274, shifting the report's
"7.0x worse per character" claim to a corrected **~10.1x**.

**Verdict:** strongest finding overall. Directly disproves REPORT_v0's
claim that tok/char "independently confirms" tok/word and that "no
further measurement is needed" — the tok/char metric itself was
significantly distorted, in a way that understated the true gap. Also
shows tok/char is unreliable even for comparing Indian languages against
each other, not just against English.

### Conceptual bug — "words" is not a language-neutral denominator
Tested tokens-per-sentence instead of tokens-per-word on the exact same
tokenized toy-corpus text, to see if the choice of denominator itself
was distorting the comparison: per-word ratio = 5.89x, per-sentence
ratio = 4.64x. Same tokens, different denominator, meaningfully
different headline number. This proves "words" is not a fair,
language-neutral unit of content — some languages pack more grammatical
meaning into fewer whitespace-separated words than others. It also
means the report's claim that tok/char "independently confirms" tok/word
is weaker than it looks, since both denominators share this same
underlying assumption problem — agreement between them isn't real
independent validation.

### Checked — NFC normalization (looks suspicious, but is fine)
`unicodedata.normalize("NFC", line)` visibly mutates the input text
before analysis, which looks alarming on first read (same category of
suspicion as the `.lower()` line). Removing it: zero change in output
(eng=1.27, hin=7.45, ratio=5.89x, identical to baseline). This is
standard defensive practice against inconsistent Unicode encoding of
visually identical characters across different real-world text sources.
**Should not be flagged as a bug** — removing it would only add risk on
messier real-world text, not reduce it.

### Minor checks (low priority — mentioned for completeness, not headline findings)
- **Macro vs. micro averaging:** script averages per-line ratios equally
  (macro), rather than pooling total tokens / total words (micro).
  Tested both on toy corpus: macro=7.448, micro=7.403 — only ~0.6%
  difference, since sentence lengths don't vary much in the toy sample.
- **Unused imports:** `random` and `sys` are imported and
  `random.seed(1337)` is set, but neither is ever used anywhere in the
  script. Zero numeric effect — likely leftover from a removed step
  (possibly random sampling of a larger source corpus). Code-quality
  observation only, not a correctness bug.

## A3 — Corrected analysis: 2 tokenizers × 4 denominators × 4 languages

Ran a3_analysis.py on the real FLORES devtest corpus (1012 sentences/
language, held-out split reserved for final numbers), comparing gpt2
(English only trained) against xlm-roberta-base (multilingual
SentencePiece tokenizer, trained on 100 languages including Hindi,
Tamil, Telugu), across four denominators: tok/word, tok/grapheme,
tok/byte, tok/sentence.

### Raw results

| tokenizer   | lang | tok/word | tok/graph | tok/byte | tok/sent |
|---|---|---|---|---|---|
| gpt2        | eng  | 1.235    | 0.205     | 0.2047   | 26.72    |
| gpt2        | hin  | 7.818    | 2.209     | 0.5947   | 198.09   |
| gpt2        | tam  | 25.048   | 4.213     | 0.9965   | 415.19   |
| gpt2        | tel  | 20.709   | 4.138     | 0.9918   | 346.60   |
| xlm-roberta | eng  | 1.400    | 0.232     | 0.2321   | 30.30    |
| xlm-roberta | hin  | 1.491    | 0.421     | 0.1134   | 37.77    |
| xlm-roberta | tam  | 2.465    | 0.415     | 0.0981   | 40.87    |
| xlm-roberta | tel  | 2.384    | 0.476     | 0.1142   | 39.90    |

### Ratios vs English

**gpt2:** hin word=6.33x graph=10.78x byte=2.90x sent=7.41x
tam word=20.28x graph=20.56x byte=4.87x sent=15.54x
tel word=16.77x graph=20.19x byte=4.84x sent=12.97x

**xlm-roberta:** hin word=1.06x graph=1.81x byte=0.49x sent=1.25x
tam word=1.76x graph=1.78x byte=0.42x sent=1.35x
tel word=1.70x graph=2.05x byte=0.49x sent=1.32x

### Key finding
Tokenizer choice changes the headline conclusion far more than
denominator choice does. gpt2 shows huge, alarming gaps (Tamil up to
20x worse than English); xlm-roberta shows much smaller gaps (Hindi
1.06x-1.81x, Tamil/Telugu 1.7x-2.0x depending on denominator) across
every denominator tested. This strongly suggests REPORT_v0's "6x worse"
conclusion is largely an artifact of testing with an English-centric
tokenizer, not a fundamental property of these languages.

Notably, byte-based ratios with xlm-roberta fall below 1.0 (0.42x-
0.49x) for all three Indian languages — despite Indian scripts using more
bytes per character in UTF-8 than Latin script, xlm-roberta still uses
fewer tokens per byte than English, because it tokenizes these scripts
efficiently. This shows byte based cost and token based cost can point
in opposite directions depending on tokenizer quality.

## A3 — which single number should we actually use?

Looked at all four denominators using xlm-roberta. word, grapheme, and
sentence all show a similar, small gap (around 1x-2x). byte is
different — it goes below 1.0 for all three Indian languages.

Decided which one to actually use:
- word: not using this. we already proved earlier (in A2) that "word"
  is not a fair way to compare languages, so even though it looks fine
  here, it would be wrong to suddenly trust it now.
- grapheme: this is fine to use, gives a similar answer to word and
  sentence.
- byte: not using this as the main number. byte measures how much
  storage space the text takes up, not how much work the model has to
  do. that's why it's giving a different answer than the others.
- sentence: this is the one I'm picking as the main number. since our
  corpus has the exact same sentence translated into every language, we
  don't need to argue about what counts as a fair "word" or "character"
  — we can just directly compare: same sentence, how many tokens does
  each language need?

**Why word and sentence don't fully agree, even for the same
language.** For Hindi, word gives 1.06x but sentence gives 1.25x — a
real gap, not noise. Hindi sentences in this corpus use more
space-separated words on average than the matching English sentences
do, because things English folds into one word (like "for the", "to
the") are often written as extra separate words in Hindi. So a Hindi
sentence's token count gets divided by a bigger word count, which
quietly shrinks the word ratio. Sentence count doesn't have this
problem — it's fixed at exactly 1 per line no matter the language.
This is another reason to trust sentence over word: word isn't just
"less clean" in theory, it's actually understating the gap here in a
way we can point to. (Noticed this gap only after re-reading the ratio
table a second time — first pass, I nearly reported word and sentence
as "basically agreeing," which they don't, quantitatively.)

**Final answer:** using xlm-roberta, tokens-per-sentence shows hindi is
about 1.25x more expensive than english, tamil about 1.35x, telugu
about 1.32x. This is the number I'm reporting as the main finding.
Word and grapheme back this up since they show similar small numbers.
Byte is mentioned separately since it's measuring something different
(storage cost, not processing cost).

This is very different from what REPORT_v0 said. They said Hindi costs
6x more and we should build a whole separate system for it. What we
found says: most of that extra cost was because they used the wrong
tokenizer (gpt2). If you just switch to a proper multilingual
tokenizer, most of the problem goes away on its own.

## A4 — Recommendation Memo

**Corrected numbers.** We tested this properly using a tokenizer that
actually understands Hindi, Tamil, and Telugu (xlm-roberta) instead of
gpt2, which only really understands English. Using the fair comparison
(same sentence translated into each language), the real gap is: Hindi
costs about 1.25x more tokens than English, Tamil about 1.35x, Telugu
about 1.32x. This is very different from what REPORT_v0 said (5.89x to
6x). Their number was wrong because they used gpt2 (bad at Indian
languages) and also had a bug in how they counted characters.

**What we recommend.** Keep the separate system for Indian languages
like the old report suggested, but fix the budget plan for about
1.3x extra cost, not 6x. Separately, we think it's worth someone
looking into switching to a better multilingual tokenizer later, since
most of the "Hindi is expensive" problem seems to actually be a
tokenizer problem, not a language problem. But we're not recommending
that switch right now — just flagging it as something worth checking
properly first.

**Biggest thing we're not sure about.** We only checked how many
tokens each language uses. We did NOT check whether the model still
gives good, correct answers if you actually changed the tokenizer.
Using fewer tokens doesn't automatically mean the model still works
well — that needs to be tested separately before anyone commits to
switching tokenizers.

**What to watch after this goes live.** Keep an eye on two things,
separately for each language: (1) how many tokens real user requests
actually use, compared to our prediction (1.25x-1.35x) — if real
traffic uses way more than we predicted, it means our corpus (formal
Wikipedia-style text) doesn't match how people actually chat. And (2)
actual GPU cost per request — since token count is just a stand-in for
real cost, checking that both match up confirms our numbers actually
translate into real savings, not just numbers on paper.

---

## B1 — KV-cache Math

First attempt: computed max concurrent sequences using only
gpu_memory_utilization (0.92) and overhead (1.6GB), without subtracting
model weights. Got ~43-47 sequences. Checked this against the log's
implied capacity (batch ÷ kv_cache_util at prompt_len=3584+gen_len=512
rows) — log consistently implies ~25.8. Way off. This was the dead
end: forgot that the model's own weights (4.2B params × 2 bytes =
8.4GB) sit in GPU memory before any KV cache can be allocated at all.

Redid it subtracting weights: 24GB × 0.92 = 22.08GB, minus 8.4GB
weights, minus 1.6GB overhead = 12.08GB for KV cache. Per-token cost:
8 KV heads × 128 head_dim × 2 (K+V) × 2 bytes × 28 layers = 114,688
bytes/token. 12.08GB ÷ 114,688 bytes ÷ 4096 tokens/seq ≈ 25.7 sequences
— matches the log's ~25.8 almost exactly.

Also checked decimal GB vs binary GiB as an alternate hypothesis for
why the naive calc was off — decimal gives 25.7 (matches), GiB would
give ~28.9 (worse match). Confirms decimal GB is the right convention,
matching how model_spec.md states GPU capacity.

## B2 — Throughput Anomaly

Reported_tok_s peaks at batch 24 (1607.4) then falls at batch 32
(1384.0) and 48 (1298.5), despite preempted_seqs going from 0 to 7 to
23 over that same range, and kv_cache_util maxing out at 0.93-0.97.
Batch 24 = ~93% utilization with zero preemptions, right at the B1
capacity ceiling (~25-26 sequences). Past that, the scheduler has to
preempt (evict + later resume) sequences, and resumed sequences must
re-run prefill — wasted work that eats wall-clock time without
producing new tokens.

Initial write-up said "reported_tok_s = tokens completed ÷ elapsed
time" — this turned out to be wrong once B3 was done (see below).
Fixed after cross-checking the two sections against each other.

## B3 — The reported_tok_s misread

Tested whether reported_tok_s counts only generated tokens or prompt+
generated tokens together, using the batch-24 row (prompt=3584,
gen=512, 24 requests, wall_clock=61.16s):
- gen-only hypothesis: 24×512/61.16 = 200.9 — doesn't match reported
  1607.4
- prompt+gen hypothesis: 24×4096/61.16 = 1607.5 — matches almost
  exactly

This directly contradicted the definition I'd written in B2 ("tokens
completed"). Went back and fixed B2's wording once this was confirmed,
since the two sections can't both be right.

True goodput at batch 24 ≈ 201 tok/s (two independent derivations:
direct from gen_len×requests/time, and reverse-engineered from
reported_tok_s × gen_len/(prompt_len+gen_len) — both give ~200.9).
This is ~8x lower than the quoted 1607 headline. Also checked
short-prompt batch 16 goodput (16×256/13.91 ≈ 294.5) — higher than the
long-prompt goodput, which reverses REPORT_v0's claim that long
prompts give better throughput. And batch 48's true goodput
(1298.5×0.125 ≈ 162) is lower than batch 24's, not the claimed ~3200 —
so the "linear scaling" extrapolation in REPORT_v0 is wrong on top of
using the wrong base number.

## B4 — Production confirmation metric

Given the log's column names already look like vLLM-style scheduler
stats (preempted_seqs, kv_cache_util), the real-world equivalent to
watch would be a live preemption counter (e.g. vLLM's
num_preemptions_total) alongside KV cache utilization — expect it to
sit near 0 below ~93% utilization then jump sharply past ~95-97%,
mirroring the log's 0→7→23 pattern.

## Part C — Decision Memo

First draft of the day-1 experiment said "3-5 prompt variants" and "2
reviewer hours" in the same paragraph — didn't actually check the
arithmetic. 4-5 variants × 20 examples × 2 min/example doesn't fit in
2 hours (comes out to 2h40-3h20). Fixed to a fixed 3 variants × 20 =
60 examples × 2 min = exactly 2 hours.

Also initially claimed fallback training would take "probably well
under a day" on the A100 with no measurement behind it — caught this
as an unearned confidence claim (violates the same evidence rule
everything else in this project is held to) and changed it to "measure
via a short pilot, then extrapolate" instead of asserting a number.

Missed serving cost for option (b) entirely on the first pass, even
though the assignment explicitly lists "training or serving cost" —
added a line acknowledging the rewriter adds a second inference pass
per response, to be measured in the fallback pilot rather than assumed
negligible.

Chose 80%/60% as the success/kill thresholds and 2 min/example as the
review-speed assumption. These are judgment calls, not derived from
the assignment or from any measurement — worth being upfront about
this specifically if asked "why 60, why not 50" in the defense, rather
than inventing a post-hoc justification.
