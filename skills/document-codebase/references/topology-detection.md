# Topology detection

Heuristics for figuring out *what* you're documenting, before you start. Run through this
checklist in Phase 1 of the skill, then confirm the answers with the user before drafting.

## Step 1 — Single repo, monorepo, or polyrepo?

You are looking at a **monorepo** if any of these are present at the root:

| Signal                                   | Toolchain                  |
|------------------------------------------|----------------------------|
| `pnpm-workspace.yaml`                    | pnpm workspaces            |
| `turbo.json`                             | Turborepo                  |
| `nx.json` / `workspace.json`             | Nx                         |
| `lerna.json`                             | Lerna                      |
| `package.json` with a `workspaces` field | npm/yarn workspaces        |
| `pom.xml` with `<modules>`               | Maven multi-module         |
| `settings.gradle(.kts)` with `include`   | Gradle multi-project       |
| `Cargo.toml` with `[workspace]`          | Cargo workspace            |
| `go.work`                                | Go workspaces              |
| `pyproject.toml` with multiple `[tool.uv.sources]` or a `members` list | uv / Poetry workspace |
| Top-level `services/`, `apps/`, `packages/`, `microservices/` directory containing >1 child project | convention-based |
| A `Tiltfile`, `skaffold.yaml`, or root-level `docker-compose.yml` listing several services that build from local paths | local orchestration of multiple services |

You are looking at a **polyrepo** (microservices spread across many repos) if:

- The user passes you several sibling git repos in a parent directory.
- The user mentions "microservice", "service mesh", "service-to-service" but the current
  repo only contains one service.
- The user references service names that don't appear anywhere in the current repo's code.

When in doubt, **ask**: "Is this the only repo I should look at, or are there sibling
service repos I should also document?"

You are looking at a **single repo** if none of the above apply: one project, one
build system, one deployable.

## Step 2 — Where do docs go?

In priority order, prefer:

1. An **existing docs location** if the project already has one. Common names:
   `docs/`, `documentation/`, `doc/`, `architecture/`, `wiki/`, `book/`, `site/content/`.
   Use whatever is already there. Do not impose `docs/` on a project that has chosen
   `documentation/`.
2. A **substantial top-level README** that already covers some of the dimensions. Prefer
   to *augment* it (link from new files into it) rather than duplicate.
3. A new **`docs/`** directory at the appropriate root, if nothing exists.

For each topology:

| Topology  | Docs root(s)                                                              |
|-----------|---------------------------------------------------------------------------|
| Single    | `docs/` at the repo root.                                                 |
| Monorepo  | `docs/` at the repo root, with a `docs/modules/<name>/` subdir per module if there are >3 modules. |
| Polyrepo  | `docs/` at each service repo's root, **plus** a system-wide index location the user designates. Ask which repo (or whether to create a new one) hosts the system-wide architecture doc. |

## Step 3 — Existing convention check

Before writing a single file, scan for:

- Existing markdown files anywhere under `docs/` (or the chosen docs root).
- Existing diagrams (`*.mmd`, `*.drawio`, `*.puml`, `*.svg` under docs/).
- A `STYLE.md`, `CONTRIBUTING.md`, or `docs/STYLE.md` that prescribes a documentation style.
- README files inside service/module directories that may already cover some dimensions.

If the project has an existing convention, **follow it**. Match the heading style, the
file naming pattern, the use (or non-use) of numeric prefixes, and the diagram tool. Your
output should look like it belongs.

## Step 4 — Service/module inventory

Once topology is settled, build a list of every distinct deployable or module. For each,
record:

- **Name** (the name the team uses, not a guess from the directory name).
- **Path** (relative to the repo root, or absolute if polyrepo).
- **Language / runtime**.
- **Build tool** (npm, gradle, cargo, make, ...).
- **Entry point** (the main file or HTTP server bootstrap).
- **What it owns** in one sentence — what part of the system's behavior lives here.

Show this inventory to the user and ask for corrections before drafting per-module docs.
Topology mistakes compound: getting the inventory wrong here means rewriting the
architecture doc later.

## Common pitfalls

- **Treating a `packages/` of shared libraries as services.** A directory containing
  utility libraries is not a microservice set — those are internal packages, and they
  belong in a single "shared libraries" section of the architecture doc, not as
  per-module documentation.
- **Treating a Lambda functions directory as a polyrepo.** A `functions/` directory
  with 30 lambdas in a single repo is a single repo, not 30 services. Document them
  collectively under one architecture file with a table of functions.
- **Treating a frontend/backend split as two services.** If the frontend and backend
  live in the same repo and ship together, they're one system with two surfaces, not
  two services. Document them in a single docs tree.
- **Asking the user to choose a topology you can detect.** If `turbo.json` is present,
  don't ask "is this a monorepo?" — say "I can see this is a Turborepo monorepo with N
  apps under `apps/` and M packages under `packages/`. Confirm the inventory below
  before I draft."
