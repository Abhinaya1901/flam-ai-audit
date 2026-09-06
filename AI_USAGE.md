# AI_USAGE.md

## Where AI helped

- **Structuring the audit around the evidence rule.** Claude helped
  isolate each claimed bug in fertility.py into a single-variable
  change (one script per hypothesis: fixed split, no lower, no NFC,
  per-sentence), which made before/after comparisons clean and
  reproducible rather than tangled together.
- **Arithmetic and derivations.** The KV-cache byte math (B1), the
  goodput derivation from reported_tok_s (B3), and the two independent
  ways of cross-checking that derivation were worked out with Claude
  and verified directly against bench_log.csv.
- **Drafting Part C's decision structure.** The three-tier success
  rule (≥80% / 60–80% / <60%) and the assumption/arithmetic/kill
  criterion format came out of iterating with Claude on the memo.
- **Repo review.** Claude read the actual pushed files (not just
  trusting filenames) and caught a factual inconsistency between two
  sections of the submission (see below).

## Where AI needed correction — and where I caught it myself

- **Claude introduced a real contradiction between B2 and B3.** B2's
  first draft described `reported_tok_s` as counting only generated
  tokens; B3 proved it actually counts prompt tokens too. Claude didn't catch this itself until I pointed the two
  sections at each other — it was generated inconsistently across two
  separate answers and needed a manual cross-check to surface.
- **Claude stated an unmeasured claim with false confidence.** An
  early draft of Part C said fallback training would "probably take
  well under a day" on the A100 — this was a guess dressed up as a
  claim, in a document whose whole premise is that claims need
  evidence. I caught this and had it rewritten to say we'd measure
  training speed on a small pilot slice instead of asserting a number
  with no basis.
- **Claude's first Part C draft had an arithmetic mismatch.** It said
  "3–5 prompt variants" and "2 hours reviewer time" in the same
  breath, but 4–5 variants don't fit in 2 hours at the stated 2
  min/example rate. I caught the mismatch and had it corrected to a
  fixed 3 variants that actually equals exactly 2 hours.
- **Claude's memo missed a required cost category on the first pass.**
  The assignment explicitly asks for "training or serving cost" — the
  first draft covered training cost but never mentioned that the
  rewriter model (option b) adds a second inference pass and therefore
  a serving-cost tradeoff. I noticed the gap against the assignment
  text and had it added.
- **Claude used an overly absolute phrase** ("only a native speaker
  reliably catches [meaning errors]") that I flagged as an unnecessary
  claim that invites an easy counter-question in the defense. Softened
  to "best positioned to catch."

## What this means for the defense

The corrections above are things I understand well enough to explain
without notes — I know why each fix was needed and can re-derive the
underlying numbers live. The parts I'm least confident defending cold
are the specific thresholds in Part C (60% / 80% / the 2-minute review
assumption) — these are reasonable judgment calls I made, not values
derived from the assignment or from data, and I'll say so directly if
asked rather than inventing a justification on the spot.