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