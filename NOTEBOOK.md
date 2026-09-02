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

## A1 — obtained real multilingual corpus

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