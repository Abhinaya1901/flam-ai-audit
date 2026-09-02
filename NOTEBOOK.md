## Reproduced baseline

Ran the original script exactly as given:
python fertility.py --corpus english=eng_sample.txt -corpus hindi=hin_sample.txt -tokenizer gpt2
Output matched REPORT_v0.md exactly: english=1.27, hindi=7.45.
This confirms the report's numbers are reproducible from the script as it is.

## Bug 1 — double space inflates word count

Noticed eng_sample.txt line 7 has a double space:
"Please keep the books  in the cupboard."
Tested `line.split(" ")` in a Python shell:
Result: ['please', 'keep', 'the', 'books', ' ', 'in', 'the', 'cupboard.']
Finding: the double space produces an empty string '' counted as a "word",
increasing len(words) from 7 to 8.
This makes fertility.py divide by an increased denominator on that line,
which understates true fertility.
Confirmed hin_sample.txt line 10 has the same issue
("किताबें  अलमारी" — double space).

Isolated the split bug by testing fertility_fixed_split.py (changed split(" ") to split()).
Before: english=1.27, hindi=7.45, ratio=5.89x.
After: english=1.28, hindi=7.60, ratio=5.92x.
Effect is small (~1-2%) on this toy corpus, but will recheck on the larger corpus
since more lines could mean more whitespace irregularities.

Re-tested on the real FLORES eng/hin dev corpus (997 lines each) using
measure_flores.py. Baseline ratio: 6.093x. After split fix: 6.094x —
even smaller effect than on the toy corpus. This contradicts my earlier
prediction that more lines would mean a bigger effect — more data
actually averaged the whitespace quirk out further.
Conclusion: real bug, but negligible in practice at any scale tested.

## Bug 2 — .lower() understates the true gap

Tested removing .lower() by testing fertility_no_lower.py
(removed the line `line = line.lower()`).
Before: english=1.27, hindi=7.45, ratio=5.89x.
After: english=1.23, hindi=7.45, ratio=6.06x.
Hindi stayed exactly the same since Devanagari has no uppercase/lowercase
distinction, confirming the mechanism. English fertility dropped since
capitalized words like NASA and GPU are more likely to be recognized as
single tokens by GPT-2. The ratio actually got worse (5.89x → 6.06x),
meaning the original report's .lower() step was understating the true
Hindi/English gap, not the other way around.

Re-tested on the real FLORES corpus (997 lines): baseline ratio 6.093x,
no-lower ratio 6.318x. Effect held and slightly strengthened at scale.
Conclusion: real, robust, materially important finding.

## Bug 3 — chars = len(line) counts codepoints, not true characters

Tested whether the tok/char denominator itself was distorted, since
REPORT_v0 uses it as an "independent confirmation" of the tok/word finding.
`chars = len(line)` counts Unicode codepoints, not human-perceived
characters (graphemes). Devanagari combines base consonants with
separate vowel-sign codepoints (matras) — tested with the `grapheme`
library on the full hin_dev.txt corpus: 125,366 codepoints vs 87,046
true graphemes, a ratio of 1.44x overcounting.
Recomputed: reported hin tok/char=1.579 corresponds to a true
tok/grapheme of ~2.274. This changes the tok/char-based ratio from the
reported 7.0x to a corrected ~10.1x.
This directly undermines REPORT_v0's claim that tok/char "independently
confirms" the tok/word finding and that "no further measurement is
needed" — the tok/char metric itself was significantly distorted.

## Extended bug 3 — checked Tamil and Telugu, same pattern confirmed and worse

Ran the same codepoint-vs-grapheme check (grapheme library) across all
four FLORES dev corpora.
Results: English ratio=1.000 (zero distortion, confirms mechanism is
script-specific, not universal). Hindi ratio=1.440. Tamil ratio=1.547.
Telugu ratio=1.566 — Telugu is actually the most affected language,
worse than Hindi.
Conclusion: chars = len(line) is structurally broken for all three
Brahmic scripts tested, not just Hindi, and the degree of distortion
varies unpredictably (1.44x-1.57x) across languages. This means
tok/char is unreliable not only for Indic-vs-English comparisons but
also for comparing Indic languages against each other — a routing
decision between Hindi, Tamil, and Telugu traffic using tok/char would
itself be built on inconsistent measurement errors.

## Checked NFC normalization — looks suspicious, but is fine

Tested removing NFC normalization in fertility_no_nfc.py.
Result: english=1.27, hindi=7.45, ratio=5.89x — identical to baseline, zero change.
This is the "looks suspicious but is fine" item. NFC normalization visibly
mutates input text, which looks alarming on first read, but is standard
defensive practice against inconsistent Unicode encoding of visually
identical characters. No change here is likely because the sample files
were already stored in NFC form, but the line should not be flagged as a
bug — removing it would only add risk on messier real-world text, not reduce it.

## Conceptual bug — "words" is not a language-neutral denominator

Tested tokens-per-sentence instead of tokens-per-word in
fertility_per_sentence.py, to check whether the words denominator itself
was distorting the comparison.
Per-word ratio: 5.89x. Per-sentence ratio: 4.64x — a meaningfully
different number, produced from the exact same tokenized text.
This proves the choice of denominator materially changes the headline
conclusion, which is the conceptual bug: "words" is not a language-neutral
unit of content, since some languages pack more grammatical meaning into
fewer whitespace-separated words than others. The report's claim that
tok/char "independently confirms" tok/word is also weaker than it looks —
both denominators share the same underlying assumption problem, so
agreement between them isn't real independent validation.

## Checked averaging method — macro vs micro average

Tested macro-average (script's method: mean of per-line ratios) vs
micro-average (pooled total_tokens / total_words) on hin_sample.txt.
macro=7.448, micro=7.403 — only 0.6% difference on this toy corpus,
since sentence lengths don't vary much here.
Flagging as a real methodological ambiguity (the script never states
which averaging convention it intends) rather than a clear bug, since
its measured impact here is small. Worth re-testing on the larger,
more length-varied FLORES corpus in A3.

## FLORES - obtained real multilingual corpus

Original plan (openlanguagedata/flores_plus) was a gated dataset requiring
HuggingFace login/terms acceptance — used Muennighoff/flores200 public
mirror instead but had to downgrade 'datasets' library to 2.19.0 since this
dataset uses an older loading script format the newest library version
no longer supports.
Downloaded dev (997 sentences) and devtest (1012 sentences) splits for
english, hindi, tamil, telugu.
Verified first 3 lines by eye across all 4 files — confirmed genuinely
parallel (same source sentence topics in same order: Stanford diagnostic
chip, JAS 39C Gripen crash, same follow-up sentences).