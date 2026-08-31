# Review record — DESIGN.md v1 (red team / blue team / adjudication)

Date: 2026-08-31. Two Opus subagents reviewed DESIGN.md v1 against
`research/00-SYNTHESIS.md`; Fable adjudicated. DESIGN.md v2 incorporates the
adjudicated outcome. This file is the durable record: what was attacked, what was
proposed, what was accepted/overruled and why. An LLM resuming this project should read
DESIGN.md (current) first and use this file to understand *why* v2 is shaped as it is.

---

## Part 1 — Red team report (verbatim)

### A. Verdicts on the five original findings

**A1 — Unbounded rewrite loops (compounding certainty inflation / content regression).
Partially solved; one hole goes straight through.** Regenerating from the skeleton does
break the paraphrase chain, and that is the right mechanism. But three channels
reintroduce path dependence. (i) Stage 7 appends the author's span-scoped *complaints*
to the skeleton and regenerates — complaints are a lossy encoding of the rejected draft,
so draft N conditions draft N+1 through a side channel the design claims is closed.
(ii) Stage 7's third outcome reopens G1 and *amends* the skeleton; the amendment is
written by an author reacting to rejected prose, so the "lock" drifts toward whatever
the last draft made salient. Nothing constrains the amended skeleton against the version
G2 certified. (iii) Stage 5 failures route back to Stage 4 with **no cap** (Stage 7 has
a cap of 3; Stage 5→4 has none) and with failure lists accumulating in the prompt.
Separately, the guard against certainty inflation is entailment, and the research names
the exact case it misses: "a restyling pass that quietly deletes a qualifier scores
perfectly on standard SummaC/AlignScore usage" (06:62). Dropped-hedge inflation
("X may contribute" → "X contributes") passes forward entailment because the categorical
entails the modal, and passes backward under high lexical overlap. The design's single
stated defence against its single strongest research finding is the instrument the
research says is blind to it.

**A2 — Voice ceiling (LUAR 0.49 vs 0.63). Papered over.** §5 argues the meld sidesteps
the ceiling because it conditions on a concrete exemplar rather than abstract style
instructions. Synthesis finding 4 says "every prompt-and-retrieve personalisation method
converges to 0.484–0.508 … a 0.024 spread across all methods" — exemplar retrieval is
inside that family, not outside it. The design's real differences from the measured set
are the engine (PersonalBench used Qwen 3 and GLM-4, not Gemini 3.1 Pro) and the
single-pass rule; that is a legitimate open question, not an answer. Worse: **DESIGN.md
contains no voice metric at all.** LUAR, Burrows's Delta, and the calibrated
non-colluding AV triple the research requires appear nowhere. Stage 6a measures
machine-ness (Binoculars, Fast-DetectGPT, Ghostbuster) and lexical tells. Ranking
anchors by that score selects for *not-machine*, never for *is-Chris*. The project's
stated goal is the one property it does not instrument. The topic-leak trap is also not
eliminated, only relocated: anchor selection by score, inside the author's own corpus,
is topic-matched retrieval, and detector/authorship signals are topic-leaky by the same
mechanism.

**A3 — Grounding is the committee-fatal defect. Ordering solved, mechanism not.**
P-2 and G2 put grounding first; correct. Three mechanism failures. (i) §4 Stage 3
requires showing the author "the nearest candidate passages" for a citation that does
not resolve — that is semantic search over the whole source corpus, and §8 explicitly
does not build it ("Not built: RAG infrastructure … per-section retrieval by citation is
enough"). You cannot retrieve by citation for the class of defect defined by the
citation being broken. Direct internal contradiction. (ii) G2 verifies the *skeleton*.
Between G2 and G6 the text is generated and melded; nothing checks that citation markers
in the final melded paragraph still resolve to the passages certified at G2. The meld is
a rewrite and can move, merge, or drop markers. The research's B8 (deterministic
entity/number/citation multiset diff, prompt-only, trivial to build) is the missing
component. (iii) "Verifiable locator" is never defined as verifiable *by whom*. P-5's
markdown-only pipeline destroys pagination, so a locator into a private markdown
conversion is as unverifiable to a committee as "Kelley markdown line 6316" was.

**A4 — Learnings become a machine signature and go stale. Partially solved, with a new
hazard.** The admission questionnaire and FDR retirement are the right shape. But FDR
needs counts, and one paper yields per-rule n of 2–5; a rule with 2 accepts and
0 rejects is immortal on noise. "Re-validated at the start of each paper" never fires if
there is one paper. The questionnaire's answerer is unspecified: if Claude answers it,
that is self-judging (violates P-3); if the author answers four written questions per
proposed learning at the end of every section review, it is a fatigue tax levied at the
fatigue maximum. The never-retired termbase is a new failure mode, not a mitigation: a
wrong termbase entry is unfixable by the specified mechanism, is enforced by Vale "at
every stage" including inside the meld, and therefore imprints uniform, mechanical
conformance across the whole document — the low-variance signature the research warns
about. No precedence rule exists for termbase vs anchor when an anchor paragraph
violates a Vale rule.

**A5 — Under-specified polish dial. Mostly solved.** Three discrete edit classes with a
diff-and-veto middle band is a real fix, and the bidirectional guard at every level is
correct. Residual: nothing distinguishes 4 from 6 (ten labels, three behaviours); the
dial's scope (span / section / paper) is undefined; and the 7–10 band melds the author's
*own* prose against another of the author's paragraphs. Baumler et al. (01:698) measured
that post-editing moves text toward the author but leaves it closer to LLM text than the
author's unassisted writing, and *reduces stylistic diversity*. The top of the dial is
the one place the design demonstrably degrades real human voice.

### B. Attacks on the tick-tock loop, by severity

1. **G2 is silently invalidated by the G1 reopen path (Stage 7 → Stage 2).** Author adds
   a concept at round 2 that has no source. Stage 4 generates it; Stage 5 checks the
   draft against "the skeleton **or** a grounded source" — the skeleton item is in the
   skeleton, so it entails itself and passes. The claim ships ungrounded, past the gate
   the design calls committee-fatal. Nothing in §4 says an amended skeleton reopens G2.
   This is the worst single defect in the loop.
2. **Stage 5 Goodharts itself by construction.** The cheapest way for Stage 4 to satisfy
   "every locked meaning item is entailed by the draft" is to restate skeleton items
   near-verbatim, and the accumulating failure list actively teaches it to. Result:
   literal, flat, machine-shaped prose that passes the content gate perfectly. Stage 6a
   cannot see it — the grader runs after the meld, on the melded text. Nothing measures
   copy rate from skeleton to draft.
3. **Stage 8 is an uncapped document-scale rewrite loop.** Transition and
   argument-diversity findings become "span-scoped tickets back into the per-section
   loop." A ticket on section 7 regenerates from section 7's skeleton — stochastically,
   so the whole section changes and the author must re-approve a section they already
   closed — and altering section 7's last paragraph can break the transition into
   section 8, generating a new ticket. No cap, no convergence argument, at exactly the
   scope where P-1's iteration discipline is absent.
4. **Stage 2 / G1 is the bottleneck and it is authorship, not review.** The author must
   supply every missing concept, missing jargon, missing argument, *and how they want it
   stated*, per section. For a 73k-word paper that is the paper's hardest cognitive
   work, front-loaded across every section before most prose exists. §10's fatigue
   mitigation ("TL;DR-first keeps the author's work at the meaning level") is inverted:
   meaning-level work is the expensive kind. If the author can reliably do Stage 2 forty
   times, they can write the paper.
5. **No retraction path for a closed G6.** The only backward edge is G1. When the author
   at section 20 decides section 3's framing was wrong, the governed options are
   nothing; they will hand-edit the markdown. A hand-edit is not represented in
   section 3's skeleton, so any later Stage-8 ticket regenerating section 3 **silently
   reverts it**. Data loss with no detector.
6. **Skipping the TL;DR is the specified fatigue attractor.** Stage 7 explicitly permits
   going straight to the complaint. Under fatigue that becomes default, and the skeleton
   is then whatever Stage 1 extracted — the machine's reading of the machine's own
   defective draft — locked as ground truth, with Stage 5 certifying fidelity to it.
   G1 requires no evidence of verification: no mandatory marking, no attention signal,
   no record that the author read the item list. Gate reports green on unverified
   meaning.
7. **Stage 6a produces confident rankings from noise.** Binoculars/Fast-DetectGPT/
   Ghostbuster at *paragraph* scope, ranking ~6 candidates: "the local gradient of a
   detector score is noise at best" (06:69). The tell-counters are worse: em-dash rate
   over a four-sentence paragraph is 0, 1, or 2. These are document-level statistics
   applied at paragraph granularity. The anchor promote/demote loop then writes that
   noise permanently into the corpus.
8. **Session-per-section erases everything cross-sectional until Stage 8.** The measured
   document-level defect (argument uniqueness 3.4% vs 65.3%; thread continuity 33% vs
   50%) is invisible to every gate G1–G6 by construction, and is deferred to the one
   stage with no convergence guarantee. Cross-section *style* consistency is not on
   Stage 8's list at all.
9. **Unbudgeted meld fan-out.** ~700–900 paragraphs × 3 anchors × optional temperature
   variation = thousands of Gemini calls, each followed by a bidirectional entailment
   re-check on a 16 GB GPU. No cost budget, no rate-limit policy, no partial-completion
   state model for a mid-section API failure.

### C. New failure modes the design introduces

1. **The skeleton is a single point of failure with no quality check, and it inherits
   the original defect.** Stage 1 extracts the skeleton *from the defective draft*. If
   Stage 1 misses a concept and the author doesn't notice, the skeleton omits it, and
   every downstream gate certifies the omission as correct. Stage 3 checks
   skeleton→sources; it never checks **sources→skeleton** (do the sources contain
   material the skeleton dropped). The design that made bidirectionality its signature
   runs its most important check in one direction.
2. **The ground truth is measured to be unreliable for the property being optimized.**
   P-3 makes author approval the only verdict. Baumler et al. (81 participants,
   pre-registered) found post-editors perceive the result as representative of their
   style while it sits closer to LLM text than their own unassisted writing. With no
   objective voice metric, G6 approval is precisely the self-report that study kills.
3. **Anchor-pool overfitting.** Promotion/demotion converges the pool to a few winners;
   a 73k-word paper melded against ~5 anchors acquires one cadence throughout. Low
   stylistic variance is itself the tell — and the anchors are the author's *best*
   writing, a non-representative tail of their distribution, not their voice.
4. **P-4 is honored rhetorically and violated operationally.** Argmax over a detector
   score *is* optimization against that detector; anchor promotion makes it a hill-climb
   with persistent memory across papers.
5. **Anchor content leakage.** The meld sees an author paragraph on a related topic. It
   may import a claim, a stance, or a confidence level from it. The output→skeleton
   check may catch an imported atomic claim; it will not catch an imported stance or
   hedge-level shift — the same certainty-inflation channel as A1.
6. **Engine dependence is deeper than §10 admits.** "Config is data, not code" does not
   survive a mid-project snapshot change: sections 1–20 and 21–40 end up in different
   voices, and Stage 8 has no cross-section style check to notice.
7. **B3 encodes the loop from n=1.** One manually-run section, then B4 freezes the
   orchestrator around it. A literature-review section and a methods section stress the
   loop completely differently.
8. **B2's gate has near-zero statistical power.** "≥9/10 seeded defects caught" over 10
   self-authored seeds: a detector with 74% true recall passes that gate ~22% of the
   time, and a 90%-recall detector fails it ~26% of the time. Self-seeded defects also
   skew easy (deleted sentences, not deleted qualifiers).

### D. Limitations — what the red team could not evaluate

- The meld system prompt does not exist in written form; no (input, anchor, output)
  triples exist to inspect. The A2 verdict cannot be closed either way.
- Author corpus size and composition unknown (research floor: ≥50k words across ≥40
  independent documents plus topic-matched negatives).
- No measured entailment accuracy on this domain (AlignScore/MiniCheck numbers are from
  summarization benchmarks; nearest calibration ~74.4% balanced accuracy, "a useful
  signal, not a reliable oracle"). Only the existence of the A1 hole is established, not
  its size.
- Paper 007's actual section count/lengths not examined; "40 sections" is hypothetical.
- G0 satisfiability unknown (does the original markdown + Kelley markdown + sources
  exist?).
- PersonalBench's exact method list not verified against exemplar conditioning — if
  excluded, A2 weakens from "papered over" to "unresolved"; the engine (Gemini 3.1 Pro)
  is genuinely unmeasured. This is the design's one legitimate escape.
- Marked speculation: paragraph-scale detector degradation is general knowledge (the
  RAID perturbation-collapse half is in-corpus); all author-behaviour predictions are
  mechanism arguments, not measurements — B3 settles them.
- Spec defect: v1 asserted "gates G0–G6" but defined only G0–G3 and G6; G4/G5 did not
  exist.

---

## Part 2 — Blue team report (condensed; recommendation verbatim in substance)

Assumed scale: ~73k words, ~35 template sections, one author. "Tick" = a bounded human
sitting; "tock" = machine work between sittings costing zero human attention.

**Candidate 1 — Serial deep loop (v1 §4).** One section fully finished per session.
Strongest: tightest error containment; a meaning error is caught in the sitting that
created it; blast radius one section. Worst: structurally cannot see cross-section
argument flatness (never puts two sections in front of the author); the human pays a
synchronous wait per section; no staleness mechanism — section 1's prose is frozen
before section 30's learning exists. ≈45–60 min attention, ≈75–90 min elapsed per
section.

**Candidate 2 — Pipelined/batched.** Two human-drained queues (meaning, approval);
tick = one sitting draining both; tock = machine processes everything locked. Strongest:
batch meaning review is the only point where document-level flatness becomes visible to
the only agent who can fix it; removes all dead wait. Worst: unbounded WIP — a meaning
error locked at tick A is discovered at tick B after a tock of scrap work; register
switch (semantic vs aesthetic judgment in one sitting) causes batch fatigue.
≈30–35 min/section.

**Candidate 3 — Triage-first (worst-first).** Machine diagnostic pass scores every
section; human walks worst-first; clean sections get a light path. Strongest: attention
proportional to defect density; the diagnostic pass yields the paper-level grounding map
free. **Disqualifying defect:** every triage signal measures text that exists; dropped
concepts and concepts never supplied are invisible to all of them — a fluent,
well-cited, low-signature section missing its load-bearing idea scores clean and skips
the one step that would catch it. Worst-first also breaks term/argument dependency order
and front-loads the ugliest material (worst motivation curve).

**Candidate 4 — Arc-pipelined walkthrough (recommended; adopted in v2).** Partition the
paper into arcs (template top-level divisions, ≤8 sections); arcs serial, sections
within an arc pipelined. Additions over C2: a global grounding prepass before any prose;
light-path routing **by template section type** (procedural/administrative), never by
diagnostic score; a staleness ledger over approved sections. Sitting order: meaning
block first (hard work on fresh attention), approval block second (sitting ends on
finished work). Prose lags meaning by exactly one tock, so any learning discovered while
approving arc N is in force for arc N+1, and everything behind is mechanically flagged
rather than hoped about. Costs: needs a board, versioned learnings with mechanical
trigger probes, and a citation→section index. Realistic saving over C1 is 15–25% of
hours; the real win is that none of the hours are spent waiting, and cross-section
defects become visible. ≈35 min/section steady state, plus ~2–3h one-time prepass and
~4–6h final pass.

Key mechanisms adopted into v2 (see DESIGN.md for the normative spec): append-only
gates; approval records `{skeleton_v, termbase_v, learnings_hash}`; learnings carry
mechanical trigger probes; `stale.json`; re-touch only matched paragraphs from the
approved skeleton, always as an author-accepted diff; veto increments the learning's
reject count (FDR); revoked approvals are logged and harvested as (draft, hand-edit)
pairs; grounding-ledger citation→section index makes a bad source fan out to
`GROUNDING_STALE` mechanically; caps ≤3 regenerations/span and ≤2 G1 reopens/section
then `AUTHOR_WRITING`; idempotent tock (regenerate-from-skeleton is deterministic
replay); commit after every item, never at end of sitting. Named simplification:
staleness probes are mechanical string/POS matchers and will miss semantically-expressed
instances; upgrade path is running the probe as an entailment query, only if measurably
under-catching.

---

## Part 3 — Adjudication (Fable)

**Accepted as must-fix (now in v2):**
1. Skeleton amendments invalidate grounding for the amended items (red B1 — worst
   defect; closes the G1-reopen → grounding bypass).
2. Deterministic hedge/qualifier diff + citation/entity/number multiset diff added
   beside entailment (red A1/A3-ii/C5 — covers exactly what entailment is blind to:
   certainty inflation and melted citation markers, including stance imported from
   anchors).
3. Voice diagnostic (calibrated LUAR + Burrows's Delta) added to the grader and to
   B1's pass gate; periodic blind A/B against the author's unassisted writing (red
   A2/C2 — the Baumler self-perception finding makes author approval alone unreliable
   for voice specifically).
4. Lightweight source-search index (BM25/embeddings over markdown sources) built for
   broken-citation candidate retrieval (red A3-i — v1's "no RAG" refusal was an internal
   contradiction; this is one small tool, not RAG infrastructure).
5. Arc-pipelined model replaces the serial loop (blue C4) — it closes red B3 (Stage 8
   uncapped rewrite → staleness ledger with diff-accept), red B5 (no retraction path →
   append-only gates, revoked approvals logged), red B8/C6 (cross-section flatness and
   style consistency get a real home), red B4/B6 partially (meaning work batched on
   fresh attention; light path by template type).
6. Sources→skeleton assist at grounding: for each grounded passage, key claims not
   represented in the skeleton are listed for the author (red C1 — the one-directional
   skeleton check inherited the original missing-concepts defect).
7. Spec repairs: gates renumbered and all defined; entailment-regen path capped (shares
   the ≤3 cap); copy-rate (skeleton→draft n-gram overlap) reported as a diagnostic
   (red B2); anchor promotion made slow/statistical with per-arc reuse caps and sampled
   (not argmax) selection (red B7/C3/C4); meld fan-out budgeted (red B9); engine
   snapshot pinned + cross-arc style consistency in the paper pass (red C6); B2's
   seeded-defect benchmark raised to ~30 including dropped-qualifier seeds (red C8);
   B3 dry-runs two contrasting section types, not one (red C7); termbase entries get an
   author-only revision path whose changes propagate through the staleness ledger
   (red A4); learnings admission questionnaire is drafted by the machine, ratified by
   the author in one keystroke per learning, batched at arc close (red A4 fatigue tax);
   G1 requires per-item marking (verified/amended/added), not a bare "looks good"
   (red B6).

**Overruled (with reasons):**
- "Complaints are a lossy side-channel from the rejected draft" — true but acceptable:
  the measured hazard is model self-conditioning on its own prior text; human-mediated
  conditioning is the design's purpose. Kept as a residual risk note.
- "G1 is authorship, not review, therefore the author could just write the paper" —
  inherent, not a defect: the author being the sole meaning authority IS the design;
  the system's value is making meaning the only hard work left.
- A2 "papered over" downgraded to **unresolved**: the red team's own limitations note
  concedes exemplar-conditioning's membership in the measured ceiling family is
  unverified and the engine is unmeasured. B1 (with the voice metric now in its gate)
  is the experiment that settles it. No architecture rests on the meld beating the
  ceiling: if it only reaches "clean, not-machine, not-yet-Chris", the pipeline still
  functions and the hand-edit pair corpus grows toward the real voice fix.

**Standing limitations (unchanged from red team D):** meld prompt unwritten; author
corpus unmeasured against the ≥50k-word floor; entailment accuracy on dissertation
prose unmeasured; author-behaviour predictions await the B3 dry run.

**Deep-research candidates identified (pending Chris's selection):**
1. Exemplar-anchored single-pass style transfer vs the LUAR ceiling family (settles A2).
2. Certainty/hedge-preservation in rewriting; epistemic-marker diffing tooling
   (instruments the A1 blind spot).
3. Entailment-model transfer to academic prose (alternative: just build B2's benchmark).
4. HITL long-document revision workflows: batching vs serial, register-switch fatigue
   (validates the arc model's attention economics).
5. Post-editing voice convergence (Baumler line): interventions that keep human editing
   from drifting toward LLM style (informs dial 7–10).
Recommended: 1 and 2.
