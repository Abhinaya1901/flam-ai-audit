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
