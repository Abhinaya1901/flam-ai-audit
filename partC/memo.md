# Part C — Decision Memo: Casual Tone in 6 Indian Languages

**Recommendation:** (c) prompt-engineering for the 3-week launch-review
window. Reserve the A100 mainly for Weeks 2–3 as a fallback to build
(b), a small standalone rewriter model, if prompting isn't enough.

## Assumptions
1. The gap is tone (too formal), not language capability — if false,
   this plan fails regardless of path.
2. Casual register is promptable, even if underrepresented by default.
3. Reviewer's 10h/week is dedicated, not shared.
4. "No external API budget" blocks paid APIs only; self-distillation
   (own model generating training pairs) uses our own compute, not
   free compute.
5. For Tamil/Telugu/Bengali/Marathi (no human reviewer), we rely on
   model self-rated casualness — unreliable in absolute terms, treated
   as low-confidence, relative-only signal, never equated with the
   Hindi/Kannada human-reviewed numbers.

## Arithmetic
- **Reviewer time is the real bottleneck:** 30h total (10h/wk × 3),
  covering only 2 of 6 languages. At ~2 min/example, that's ~900
  examples total; ~300 in the first 10h before the kill decision.
- **GPU time is not scarce, but unmeasured:** fallback rewriter
  (≤1B params, ~1,500–2,000 synthetic pairs/language, ~10–12k total)
  — training time to be confirmed via a short pilot (measure
  examples/sec, extrapolate) rather than assumed.
- **Serving cost for (b) is unmeasured:** adds one inference pass/
  response; latency and GPU cost to be measured in the fallback pilot,
  not assumed negligible.
- Prompt iteration costs ~0 compute and no training, but still needs
  native-speaker review for meaning preservation — the error type
  native review is best positioned to catch.

## Why not (a) or (b) as primary
(a) Full SFT touches the main model directly — a regression in an
unreviewed language ships silently and isn't reversible pre-launch.
(b) as primary needs more per-language validation than 2/6 reviewed
languages can support in 3 weeks — good fallback, risky as the bet.

## Success metric
50 test sentences/language. Per example: casualness ≥4/5, meaning
preservation ≥4.5/5 (Hindi/Kannada, reviewer-scored).
**Success = ≥80%** of examples meet both thresholds → ship prompting.
**60–80%** → keep iterating. **<60%** → kill (below).
Unreviewed languages: model self-rated casualness delta + length-ratio
sanity check (≤30% longer than original), flagged low-confidence.

## Kill criterion
<60% of Hindi/Kannada examples meet both thresholds after the first 10
reviewer-hours (~days 1–3) → drop prompting, end of Week 1. GPU stays
mostly reserved for Weeks 2–3, but a minimal Week-1 pilot slice starts
early if Day-1 results already look clearly bad — so the fallback
isn't starting from zero if triggered.

## Day-1 experiment
3 prompt variants × 20 replies (Hindi + Kannada) = 60 outputs, ~2
reviewer-hours to rate. Tells us same-day whether prompting works at
all, or whether to start the fallback pilot immediately.