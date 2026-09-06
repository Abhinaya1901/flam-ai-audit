## A2 — Script/Metric Audit (fertility.py)

**Baseline reproduced.** Original script on the toy corpus matches
REPORT_v0.md exactly: eng=1.27, hin=7.45, ratio=5.89x.

### Bug 1 — double space inflates word count
`eng_sample.txt` line 7 has a double space; `line.split(" ")` turns it
into a fake empty-string "word," inflating `len(words)`. Same issue in
`hin_sample.txt` line 10. Isolated fix (`split(" ")` → `split()`):
- Toy corpus: eng 1.27→1.28, hin 7.45→7.60, ratio 5.89x→5.92x
- Real FLORES corpus (997 lines): ratio 6.093x→6.094x — smaller effect
  at scale, not larger

**Verdict:** real, confirmed bug — negligible impact at any scale
tested.

### Bug 2 — `.lower()` understates the true Hindi/English gap
Removing `line = line.lower()`:
- Toy corpus: eng 1.27→1.23, hin unchanged (7.45), ratio 5.89x→6.06x
- Real FLORES corpus: ratio 6.093x→6.318x — held and strengthened at
  scale

Hindi is unaffected since Devanagari has no case distinction —
confirms the mechanism. English fertility drops without lowercasing
because capitalized words (e.g. "NASA", "GPU") are more likely to be
single GPT-2 tokens. The ratio gets **worse**, not better — the
report's `.lower()` step was understating the true gap.

**Verdict:** real, robust, materially important — strong finding.

### Bug 3 — `chars = len(line)` counts codepoints, not real characters
Devanagari/Tamil/Telugu combine a base consonant + vowel-sign
codepoint into one visual character (grapheme), so `len()` overcounts
"characters" for these scripts. Codepoint vs. true grapheme count
(FLORES `dev`, via the `grapheme` library):

| language | codepoints | graphemes | ratio |
|---|---|---|---|
| English (control) | 125,194 | 125,194 | 1.000 |
| Hindi | 125,366 | 87,046 | 1.440 |
| Tamil | 146,128 | 94,467 | 1.547 |
| Telugu | 127,176 | 81,234 | 1.566 |

English's exact 1.000 confirms this is script-specific, not general.
All three Indian scripts overcount, and the degree varies
unpredictably (Telugu worst, not Hindi).

Recomputed: reported hin tok/char of 1.579 → true tok/grapheme ~2.274,
shifting REPORT_v0's "7.0x worse per character" claim to **~10.1x**.

**Verdict:** strongest finding. Disproves REPORT_v0's claim that
tok/char "independently confirms" tok/word — the metric itself was
distorted, understating the true gap, and is unreliable even between
Indian languages, not just vs. English.

### Conceptual bug — "words" is not a language-neutral denominator
Tokens-per-sentence vs. tokens-per-word on the same tokenized text:
per-word ratio = 5.89x, per-sentence ratio = 4.64x. Same tokens,
different denominator, materially different headline number — "words"
is not a fair, language-neutral unit; some languages pack more
grammatical meaning into fewer whitespace-separated words. Also
weakens REPORT_v0's "tok/char independently confirms tok/word" claim,
since both denominators share this same assumption problem.

### Checked — NFC normalization (looks suspicious, but is fine)
Removing `unicodedata.normalize("NFC", line)`: zero change in output
(identical to baseline). Standard defensive practice against
inconsistent Unicode encoding across real-world sources. **Not a
bug** — removing it only adds risk on messier real-world text.

### Minor checks (low priority)
- **Macro vs. micro averaging:** macro=7.448, micro=7.403 — ~0.6%
  difference on the toy corpus.
- **Unused imports:** `random`/`sys` imported, `random.seed(1337)` set,
  never used. Zero numeric effect — code-quality note only.