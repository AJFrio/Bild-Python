# Active execution plans

Put one markdown file per in-flight change that needs more than a single
PR of context. Name it `YYYY-MM-DD-short-slug.md`.

Each plan should include: goal, non-goals, files likely to change, how to
verify (`python tools/check.py --all`), and a decision log.

When the work merges, move the file to `../completed/` and add a line to
`../tech-debt-tracker.md` if anything was deferred.
