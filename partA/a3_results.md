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
way we can point to.

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