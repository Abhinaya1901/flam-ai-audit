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
encoding artifact, not a general issue. All three Indic scripts
overcount substantially, and the degree varies unpredictably between
them (Telugu is worst, not Hindi).

Recomputing with true graphemes: reported hin tok/char of 1.579
corresponds to a true tok/grapheme of ~2.274, shifting the report's
"7.0x worse per character" claim to a corrected **~10.1x**.

**Verdict:** strongest finding overall. Directly disproves REPORT_v0's
claim that tok/char "independently confirms" tok/word and that "no
further measurement is needed" — the tok/char metric itself was
significantly distorted, in a way that understated the true gap. Also
shows tok/char is unreliable even for comparing Indic languages against
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

## A3 — Final question: which single metric should drive the decision?

Comparing xlm-roberta ratios across all four denominators (word, grapheme,
byte, sentence) shows word, grapheme, and sentence all converge on a
similar, much smaller gap (roughly 1.0x-2.1x) once a proper multilingual
tokenizer is used a sharp contrast to gpt2's inflated 6x-20x gaps.
Byte is the outlier, falling *below* 1.0 for all three Indian languages.

Considered which single number to recommend:
- tok/word: disqualified despite looking reasonable here — already
  proved (conceptual bug, A2) that "word" isn't a fair, language-neutral
  unit in principle. Using it here just because the number happens to
  look convenient would be inconsistent with that earlier finding.
- tok/grapheme: principled (uses true character counts, not the
  overcounted codepoints from bug 3) and gives a similar, consistent
  answer. Strong second choice.
- tok/byte: actively misleading here — it measures Unicode encoding
  overhead (how many bytes a script needs to store one character), not
  processing cost. Disagrees with the other three metrics because it's
  measuring a genuinely different thing (storage/transfer cost, not
  compute cost).
- tok/sentence: chosen as the headline metric. Since the corpus is a
  professionally translated, truly parallel set (same content, sentence-
  for-sentence, across all languages), this metric sidesteps the entire
  "what counts as a fair word/character" debate — it directly answers
  "for saying the same thing, how many tokens does each language need?"
  with no assumptions about linguistic units required.

**Conclusion:** with xlm-roberta, tok/sentence ratios vs English are
hin=1.25x, tam=1.35x, tel=1.32x. Recommend reporting this as the
headline number, with grapheme and word ratios cited as supporting/
convergent evidence, and byte explicitly flagged as measuring encoding
cost rather than processing cost.

This reverses REPORT_v0's recommendation: rather than "budget 6x extra
serving cost and route to a separate Indian model," the evidence
suggests switching to a multilingual tokenizer resolves most of the
apparent cost gap on its own.
