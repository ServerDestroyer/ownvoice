# B4 — The walkthrough skill

**Objective:** encode what B3 proved into the orchestrator. Prereq: B3 (do not build
this before the dry run — the loop must be proven, then frozen; and fold in any DESIGN
amendments B3 produced).

**Form:** a Claude Code skill (`SKILL.md` at repo root or `.claude/skills/`) driving
stdlib Python tools in `tools/`. The skill is the tick/tock conductor; the tools own
state.

**Build (spec: DESIGN.md §4, all of it is normative):**
1. **State** — exactly the §4 "Persisted state" tree: `state/board.json`, `state/arcs.md`,
   `state/grounding-ledger.json`, `state/termbase.yml`, `state/learnings/`,
   `state/stale.json`, `sections/<id>/*` with versioned artifacts and
   `approval.json {skeleton_v, termbase_v, learnings_hash}`.
2. **Tock script** (`tools/tock.py`) — for each MEANING_LOCKED section: ground → draft
   (inputs: skeleton + grounded sources + complaints-as-constraints + anchors, NEVER a
   prior draft) → guard (B2) → meld sweep (B1 config; default 2 anchors, sampled with
   per-arc reuse caps, widen only on flags) → guard each candidate → grade → rank →
   REVIEW_READY. Idempotent: crash = re-run.
3. **Tick script** (`tools/tick.py`) — print board → meaning block (arc N+1, per-item
   questions) → holds block → approval block (arc N) → commit after EVERY item. Encode
   the §4 tick mechanics: seeded defects at ~1-in-10–15 from `tools/seeds/` with
   feedback; commit-before-reveal; side-by-side layout; two micro-diversion prompts;
   end on an approved section + open the next skeleton. Blocks ≤50 min, sitting ≤90:
   the script tracks elapsed time and says stop.
4. **Gates and invariants** — assert I1–I8 in code (they are listed in DESIGN §4);
   gates are append-only records; skeleton amendment invalidates grounding for amended
   items; caps ≤3 regens/span, ≤2 reopens → AUTHOR_WRITING with the §8 dial.
5. **Learnings + termbase** — admission questionnaire drafted by machine, ratified
   one-keystroke at arc close; trigger probes; `stale.json` retouch-diff flow; Vale for
   the termbase; termbase beats anchors, conflicts logged.
6. **2-AFC calibration** — 8–10 pairs at paper start, 4–6 per arc, cumulative, catch
   trials (research/14 protocol; identification question, never preference).

**Gate:** one full arc of stand-in material runs gate-to-gate through the skill with no
manual state handling; every invariant assertion demonstrably fires when provoked
(write one negative test per invariant).

**Record in BUILD.md:** what B3 amendments were encoded; invariant test results.
