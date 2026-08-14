# Knowledge base catalog

`docs/` is the system of record. `AGENTS.md` is only a map.

| Doc | Status | What it covers |
| --- | --- | --- |
| [../ARCHITECTURE.md](../ARCHITECTURE.md) | current | Layers, HTTP contract, test map |
| [../AGENT_SETUP.md](../AGENT_SETUP.md) | current | Playbook to hand another agent for end-user install + `verify()` |
| [../AGENT_USAGE.md](../AGENT_USAGE.md) | current | Playbook for agents calling the SDK after setup (branches, IDs, writes) |
| [PRODUCT.md](PRODUCT.md) | current | Who the SDK is for and what "done" means |
| [DESIGN.md](DESIGN.md) | current | Design principles and taste |
| [CONVENTIONS.md](CONVENTIONS.md) | current | Naming, files, errors, JSON |
| [QUALITY_SCORE.md](QUALITY_SCORE.md) | current | Grades and gaps per area |
| [SECURITY.md](SECURITY.md) | current | Tokens, secrets, live-test rules |
| [RELIABILITY.md](RELIABILITY.md) | current | Timeouts, errors, live vs unit |
| [design-docs/index.md](design-docs/index.md) | current | Design-doc catalog |
| [design-docs/core-beliefs.md](design-docs/core-beliefs.md) | current | Agent-first operating principles |
| [design-docs/http-client.md](design-docs/http-client.md) | current | Transport, headers, resolvers |
| [design-docs/auth.md](design-docs/auth.md) | current | JWT loading and error mapping |
| [exec-plans/active/README.md](exec-plans/active/README.md) | current | How to file an active plan |
| [exec-plans/completed/README.md](exec-plans/completed/README.md) | current | Finished plans |
| [exec-plans/tech-debt-tracker.md](exec-plans/tech-debt-tracker.md) | current | Known debt |
| [product-specs/index.md](product-specs/index.md) | current | Spec catalog |
| [product-specs/python-sdk.md](product-specs/python-sdk.md) | current | Intended SDK UX |
| [references/bild-api.md](references/bild-api.md) | current | Upstream API pointer |
| [references/harness-commands.md](references/harness-commands.md) | current | Local and CI commands |
| [references/eval-harness.md](references/eval-harness.md) | current | How we evaluate the SDK |

When you add a doc, add a row here and a pointer in `AGENTS.md` if agents
should discover it on every task.
