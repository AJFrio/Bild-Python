# Core beliefs

1. **The repo is the system of record.** If it is not in git, agents cannot
   see it. Prompts and chat decisions belong in a design doc or exec plan.
2. **`AGENTS.md` is a table of contents.** Long rules go in `docs/` and are
   enforced by linters.
3. **Invariants beat style debates.** Encode the ones that prevent API
   breakage (headers, public exports, read-only live tests).
4. **Do not invent Bild endpoints.** The External API reference is upstream.
5. **Corrections are cheap; waiting is expensive.** Prefer a follow-up PR
   over blocking on perfect structure, then pay debt via the tracker.
6. **Remediation text is part of the interface.** A failing lint that only
   says "error" is a harness bug.
