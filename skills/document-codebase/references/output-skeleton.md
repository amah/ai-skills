# Output skeleton

The recommended `docs/` directory layout. Adapt aggressively to what the project actually
contains — **do not create empty files** for dimensions the codebase doesn't have.

## Single repo or monorepo with few modules

```
docs/
├── README.md                       # index, one-line per file
├── 01-system-overview.md           # what this is, who uses it, the 5-minute pitch
├── 02-architecture.md              # services/modules, deployment, request lifecycle
├── 03-ui-and-journeys.md           # UI surfaces + dominant user journeys
├── 04-data-model-app.md            # domain entities and relationships
├── 05-data-model-db.md             # tables/columns/indexes/migrations
├── 06-commands.md                  # write-side operations
├── 07-queries.md                   # read-side operations
├── 08-effects.md                   # emails, jobs, webhooks, third-party calls
├── 09-business-rules.md            # invariants and validations
├── 10-apis.md                      # public interfaces
├── 11-integrations.md              # external systems
├── 12-operations.md                # local dev, deploy, runbook
└── 13-glossary.md                  # domain vocabulary
```

The numeric prefixes are deliberate — they make the file order match the reading order in
the SKILL procedure, so a new reader naturally reads them top-to-bottom.

## Monorepo with many modules

When a monorepo has more than ~3 distinct services/modules, split per-module:

```
docs/
├── README.md                       # system-wide index, links to per-module docs
├── system/
│   ├── 01-overview.md              # system-wide pitch
│   ├── 02-architecture.md          # how the modules fit together
│   ├── 11-integrations.md          # external systems used by the whole system
│   └── 12-operations.md            # cross-cutting ops
├── modules/
│   ├── <module-a>/
│   │   ├── README.md
│   │   ├── data-model.md
│   │   ├── commands-queries-effects.md
│   │   ├── business-rules.md
│   │   └── api.md
│   └── <module-b>/
│       └── ...
└── glossary.md
```

System-wide concerns (architecture, integrations, ops) live under `docs/system/`.
Module-specific concerns live under `docs/modules/<name>/`. The system-level architecture
file is the only place where inter-module communication patterns are spelled out.

## Polyrepo (microservices)

Each service repo gets its own `docs/` tree using the single-repo layout above. In
addition, designate one repo (or a separate "platform" / "docs" repo) as the system-wide
index:

```
<docs-repo>/
├── README.md                       # links to every service's docs
├── system/
│   ├── 01-overview.md
│   ├── 02-architecture.md          # service map, sync vs async, ownership
│   ├── 11-integrations.md
│   └── 12-operations.md
└── contracts/
    └── <event-or-api-name>.md      # contracts owned at the system level
```

The system-wide architecture doc is the **only** place where service-to-service flows are
described end-to-end. Each service's `docs/02-architecture.md` should describe only what
*that* service knows about its neighbors (the API or event contracts it consumes/produces).

## What goes in each file

### `README.md` (index)
A one-paragraph "what is this docs tree" header, then a flat list of every file with a
one-line description. No content lives here that isn't elsewhere — it's purely
navigation.

### `01-system-overview.md`
- One-sentence pitch.
- Two-paragraph "what this system does and why it exists".
- The primary user types (humans, other services, jobs).
- The top 3–5 use cases by traffic or business value.
- A list of what this system is *not* responsible for (just as important).
- Link to the project README rather than restating it.

### `02-architecture.md`
- Service / module inventory: name, language, runtime, what it owns.
- Deployment topology: where things run, how they're scaled.
- The dominant request lifecycle, end to end. One Mermaid sequence diagram is justified
  here if the lifecycle crosses 3+ services.
- Sync vs async boundaries: which calls block, which fire events.
- Persistence layout: which service owns which database/topic/bucket.
- Authentication/authorization in one paragraph (deep dive lives in `10-apis.md`).

### `03-ui-and-journeys.md`
- UI surfaces: web app(s), mobile app(s), admin tool, CLI, embeds. One paragraph each.
- Top 3–5 user journeys, step by step. For each step: what the user sees, which
  endpoint/handler is called, what state changes, what feedback the user gets.
- Routing convention (per-page or per-feature, server-rendered vs SPA, etc.).
- Where the UI source lives in the repo.

### `04-data-model-app.md`
- The domain entities the code reasons about — use the names the code uses.
- Relationships between entities (composition, references, aggregates).
- Entity lifecycle: how it's created, what states it transitions through, when it's
  archived/deleted.
- A small diagram (Mermaid `erDiagram` or class diagram) only if the relationships are
  not obvious from prose.

### `05-data-model-db.md`
- Tables / collections / streams, grouped by aggregate.
- For each: columns/fields, key indexes, partition/shard key if relevant, retention policy.
- Notable migrations (the ones that explain otherwise-confusing schema decisions).
- Discrepancies between the application model and the storage model. **This is where
  surprises live** — call them out explicitly.

### `06-commands.md` / `07-queries.md` / `08-effects.md`
For each operation:
- **Name** (using the code's name).
- **Trigger** (HTTP route, CLI subcommand, event consumer, scheduled job, UI button).
- **Inputs**.
- **Preconditions / authorization**.
- **State changes** (commands) or **read sources** (queries) or **external calls** (effects).
- **Outputs / events emitted**.
- **Failure modes**.

Group by aggregate or feature, not alphabetically. If the code does CQRS, follow it; if
not, the split into commands/queries/effects is still a useful organizing axis.

### `09-business-rules.md`
- One section per aggregate or domain area.
- Each rule stated as a single sentence in the code's vocabulary, followed by a citation
  (file path + function/test name) where it's enforced.
- Rules with multiple enforcement points get all of them listed — the duplication is
  itself a documentation finding.

### `10-apis.md`
- Public HTTP/GraphQL/gRPC endpoints, grouped by resource.
- For each: method, path, auth, request and response shape (compact, not bloated), error
  cases (status codes + meanings).
- Generate from OpenAPI/`.proto` files where they exist — link to the spec rather than
  restating field-by-field.
- Webhook payloads the system *sends* live in `08-effects.md`; webhook payloads the
  system *receives* live here.

### `11-integrations.md`
- One section per external system. Title is the system name.
- Purpose, direction (inbound / outbound / bidirectional), authentication method, what
  fails when it's down, who owns the contract (us or them), where credentials live.
- Distinguish "called synchronously in the request path" from "called from a background
  job" — the failure-handling implications are very different.

### `12-operations.md`
- Local dev: how to run the thing on a laptop in under 10 minutes. Commands, env vars,
  seed data.
- Deployment: who deploys, how, where to. Rollback procedure.
- Observability: where the logs are, where the metrics are, where the traces are.
- Runbook: the top 3–5 alerts that page someone, with first-response steps.

### `13-glossary.md`
A two-column table: **Term** | **Meaning**. Pull from class names, table names, event
names. Each entry: 1–2 sentence definition + one source file path.

## Framework variant

When the codebase you're documenting is a **library or framework** (consumed by other
developers, not by end-users), several dimensions need to be reframed before they
make sense. Apply these substitutions:

| Generic dimension | Framework reframe | Example |
|---|---|---|
| `01-system-overview` | What the framework PROVIDES, who CONSUMES it (developers), the in-the-box list of packages, and what it is *not* responsible for | "@hamak/app-framework provides a microkernel host + Redux state plane for browser/desktop apps. It is not a UI component library." |
| `02-architecture` | The framework's **internal** architecture: how its own pieces fit together. Avoid documenting the consuming application — that's the consumer's job. | Plugin lifecycle, DI container, package layering. |
| `03-ui-and-journeys` → **`03-developer-journey`** | A step-by-step walkthrough of how a consumer builds an app on top of the framework. NOT end-user UI flows — those don't exist. | "Step 1: bootstrap a host. Step 2: write your first plugin. Step 3: …" |
| `04-data-model-app` | If the framework HAS a state model (like a store), describe its shape and APIs here. If it's stateless, skip this dimension entirely. | The virtual filesystem store: nodes, paths, extension state. |
| `05-data-model-db` | **Usually N/A.** Most client-side frameworks have no DB. Skip and say so. | — |
| `06-commands` / `07-queries` / `08-effects` | For frameworks with a state plane, document the framework's *own* mechanisms for these (e.g. action creators, selector factories, middleware). For stateless frameworks, **collapse into one `06-extension-points.md`** file describing what consumers can plug into. | Framework's adapter actions; commands registry; hooks. |
| `09-business-rules` → **`09-framework-invariants`** | The contracts and invariants the framework guarantees, and the lifecycle/order rules consumers must follow. | "Plugins cannot resolve DI in `initialize()` — only in `activate()`." |
| `10-apis` | The framework's **public TypeScript API surface** package by package. Generate from `.d.ts` where possible. | Exported types, classes, hooks, tokens. |
| `11-integrations` | Things the framework integrates with (Redux, React, browser APIs, Tauri, etc.) and the contracts at each integration point. | "Uses `EventSource` for SSE transport; consumers can substitute via the `IEventTransport` SPI." |
| `12-operations` | **Splits in two**: (a) consumer operations — how an app built on top of the framework runs locally / deploys, and (b) framework maintainer operations — how to publish releases, manage versions, run the test suite. Treat as separate sections. | Consumer: install + bootstrap. Maintainer: `nx release publish`, conventional commits. |
| `13-glossary` | Terms the framework coins. Especially important for frameworks because consumers will encounter them in the API and need a definitive reference. | "Host", "Plugin", "Microkernel", "Extension state pattern". |

Two more rules specific to frameworks:

- **Use the framework's exact vocabulary.** If the code calls something a "host", do not
  call it a "container" or "engine" in the docs. Vocabulary mismatches make consumers
  search for things that don't exist.
- **Per-package docs are first-class.** A consumer reaches for a package by name; their
  first read is `packages/<name>/docs/README.md`. The root `docs/` tree is the *index*
  and the *cross-cutting concerns*; the per-package docs are where the bulk of the API
  reference lives. Plan accordingly — root docs are smaller in a framework than in a
  product.

## Style

- Sentence-case headings.
- Hard-wrap long paragraphs at ~90 columns for diff legibility.
- Code/identifiers in backticks; file paths as `path/to/file.ext:LINE`.
- Mermaid for diagrams only when prose would be clearly worse — and never for trivial
  three-box pictures.
- Date-stamp the index file at the top: `_Last updated: YYYY-MM-DD by <author/agent>_`.
