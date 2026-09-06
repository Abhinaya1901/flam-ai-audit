## A3 — which single number should we actually use?

Across all four denominators (xlm-roberta): word, grapheme, and
sentence show a similar, small gap (~1x-2x). Byte is the outlier — it
falls below 1.0 for all three Indian languages.

- **word:** not using this. A2 already showed "word" isn't a fair
  cross-language unit — this number looking clean here doesn't change
  that.
- **grapheme:** fine to use, agrees with word and sentence.
- **byte:** not the headline number — it measures storage space, not
  model work, which is why it disagrees with the others.
- **sentence:** the headline metric. Since the corpus has the exact
  same sentence translated into every language, this sidesteps the
  "what counts as a fair word/character" debate entirely.

**Why word and sentence don't fully agree, even for the same
language.** For Hindi, word gives 1.06x but sentence gives 1.25x — a
real gap, not noise. Hindi sentences in this corpus average more
space-separated words than the matching English sentences, since
things English folds into one word (e.g. "for the," "to the") are
often written as separate words in Hindi. That inflates the word-count
denominator and quietly shrinks the word ratio. Sentence count doesn't
have this problem — fixed at exactly 1 per line regardless of
language. Another reason to trust sentence over word: word isn't just
"theoretically less clean," it's measurably understating the gap here.

**Final answer:** using xlm-roberta, tokens-per-sentence puts Hindi at
~1.25x English, Tamil ~1.35x, Telugu ~1.32x. Word and grapheme back
this up with similar small numbers; byte is reported separately since
it measures a different thing (storage cost, not processing cost).

This reverses REPORT_v0's conclusion. They claimed Hindi costs 6x more
and recommended a whole separate system for it. Most of that gap was
the wrong tokenizer (gpt2) — a proper multilingual tokenizer closes
most of the difference on its own.