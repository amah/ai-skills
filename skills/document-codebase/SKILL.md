---
name: document-codebase
description: |
  Use when the user asks to document an existing codebase, write a README/architecture
  doc retroactively, refresh stale documentation, or produce technical documentation
  for one or many services. Covers single repos, monorepos with modules, and polyrepo
  microservice sets. Produces human-facing documentation under docs/ that captures
  architecture, UI, user journeys, data model (DB + application), commands/queries/
  effects, business rules, APIs, and integrations with other systems.
version: 0.1.0
targets: [claude, opencode]
tags: [workflow, documentation]
---

# document-codebase

You are producing **human-facing technical documentation** for an existing codebase. The
audience is engineers (and AI assistants reading over their shoulder) who need to add
features, fix bugs, and onboard without re-deriving the system from source every time.

The default output is a `docs/` directory at the appropriate root, structured around the
dimensions in `references/output-skeleton.md`. **Do not** invent dimensions that aren't
present in the code, and **do not** fabricate facts to fill out a section — leave a `TODO:`
marker and a one-line note explaining what you'd need to confirm.

## Two entry conditions

**Greenfield**: no `docs/` directory exists, or it exists but is empty / a stub. Produce
the full skeleton from scratch.

**Refresh**: a `docs/` tree already exists. **Do not regenerate it.** Read every existing
doc file, then walk the code looking for drift: new modules, removed modules, schema
changes, new endpoints, new external integrations, business rules that have moved. Propose
*targeted edits* to specific files, not a full rewrite. Show the user a punch list of
proposed changes and let them approve before writing anything.

The two modes share the same dimension list and the same skeleton. Only the *delta* changes.

## Scope discipline — critical for monorepos and large codebases

Documentation is unbounded work. A 17-package monorepo can absorb weeks of effort if you
let it. Set scope explicitly **before** drafting:

- **Single repo, ≤5 modules**: draft every dimension and every module's per-module doc in
  one pass.
- **Monorepo, 5–15 modules**: draft the full root tree + **one exemplar** per-module doc
  in depth, then **stub the rest** with a structured "what needs to be drafted here"
  list. The stubs make subsequent passes a fill-in-the-blank exercise. Tell the user
  this upfront so they don't expect 15 detailed docs in one turn.
- **Monorepo, >15 modules**: same as above, plus pick the 3 *foundational* modules
  (the ones every other module depends on) for the exemplar pass. The remaining stubs
  link back to the foundational ones for cross-references.
- **Polyrepo**: per-repo work is its own pass. Don't try to document N service repos in
  one session.

The output format for a stub is **not a placeholder you'll fill later vaguely** — it's a
checklist of specific source files to read and concrete questions to answer when the next
pass runs. A good stub shrinks the next pass to "follow the list".

## Procedure

### Phase 1 — Topology discovery

Before writing anything, figure out what you're documenting. See
`references/topology-detection.md` for the full heuristics. You need to answer three
questions:

1. **Single repo, monorepo, or polyrepo set?**
   - Single repo: one project, one root.
   - Monorepo: one repo, many internal modules/services. Look for `pnpm-workspace.yaml`,
     `turbo.json`, `nx.json`, `lerna.json`, root `pom.xml` with `<modules>`, Cargo
     workspace, `go.work`, a top-level `services/` or `apps/` or `packages/` directory.
   - Polyrepo: multiple separate repos, usually passed to you as a directory containing
     several git repos, or referenced one at a time. If the user mentions
     "microservices" but you only see one repo, ask whether there are sibling repos to
     document.

2. **Where do docs go?**
   - Single repo / monorepo: `docs/` at the repo root, with subdirs per module/service if
     there are many.
   - Polyrepo: `docs/` at the root of *each* repo, plus optionally a top-level overview
     repo or directory the user designates as the system-wide index.

3. **What's the existing convention?** If the repo already has `docs/`, `documentation/`,
   `architecture/`, a wiki dir, or a `README.md` with substantial content — use that
   location, don't impose `docs/`.

Confirm your answers with the user before proceeding to Phase 2. **Do not skip this
confirmation** — getting topology wrong wastes a lot of work.

### Phase 2 — Per-dimension drafting

For each documentation dimension (full list below), follow this loop:

1. **Gather**: read the source files that drive this dimension. Specific guidance per
   dimension below.
2. **Draft**: write the section using only what you observed. If a claim isn't
   directly supported by code or config, mark it `TODO:` and ask the user.
3. **Verify**: surface specific claims to the user *only when the source can't directly
   support them*. Verify per-doc, not per-section — 2–4 verification questions for an
   entire dimension file is usually right; 2–4 per section drowns the user. For claims
   you can't directly cite to a file, write `TODO:` inline in the draft so the user can
   review them during their pass instead of answering them in real time.
4. **Cross-link**: when a section references another (e.g. a command produces an event
   consumed by another service), add a link to the target file/section.

Dimensions to cover, in this order (skip any that don't apply to the project — but say
why you're skipping in your draft so the user can correct you):

1. **System overview** — what the system does, who uses it, the 5-minute pitch. One short
   page. Read the top-level README, the deployment manifests, and the user-visible entry
   points (web routes, CLI commands, public APIs).

2. **Architecture** — services / modules, how they're deployed, what runs where, sync vs
   async boundaries, the request lifecycle for the dominant use case. Include a Mermaid
   diagram if it clarifies things. Read deployment configs (docker-compose, k8s manifests,
   Terraform, serverless.yml, fly.toml), service entrypoints, and inter-service client code.

3. **User interface & user journeys** — what UI exists (web, mobile, CLI, admin tool),
   what the dominant user journeys are, which screens/endpoints back each step. Read the
   frontend routes / page components / view templates, and follow at least two end-to-end
   journeys from UI through to persistence.

4. **Data model — application level** — domain entities, their relationships, ownership
   boundaries (which service owns which entity in a polyrepo). Use the language the *code*
   uses, not generic ER terms. Read the model/entity/domain layers — ORM models,
   dataclasses, structs, schema files, GraphQL types.

5. **Data model — database level** — actual tables/collections/topics, columns, indexes,
   partition keys, retention, foreign-key boundaries. Read migration files (chronological
   order tells the story), schema dumps, and any DDL. Note discrepancies between the
   application model and the DB model — they're often where bugs live.

6. **Commands** — the write-side operations the system supports. What state changes can
   be triggered, by whom, with what preconditions. Read controllers/handlers/use-cases,
   anything that mutates persistent state. Group by aggregate/entity. For each command:
   trigger, preconditions, state changes, events emitted.

7. **Queries** — the read-side operations. What can callers ask the system. Read
   read-models, query handlers, GraphQL resolvers, REST GET endpoints, search indexes.
   Distinguish "live" queries from materialized read-models if the project does CQRS.

8. **Effects** — side effects that aren't direct state changes: emails sent, push
   notifications, webhooks fired, background jobs enqueued, files written, third-party
   API calls. Read mailers, job queues, webhook clients, integration services. For each
   effect: trigger, target system, payload shape, retry/failure behavior.

9. **Business rules** — invariants and validations that aren't structural. Things like
   "an order can't be cancelled after fulfillment", "a user can hold at most one active
   subscription", "discounts stack only within the same campaign". These are usually
   enforced in domain services, validators, or guard clauses. Read the validation layer,
   service-layer guards, and assertion-style tests (which often document rules in their
   names). One file or section per aggregate.

10. **APIs** — public interfaces exposed to the outside world or to other services.
    HTTP/REST, GraphQL, gRPC, message contracts, webhook payloads. Read OpenAPI specs,
    `.proto` files, schema registries, route tables. For each endpoint: method, path,
    auth, request shape, response shape, error cases. Generate from spec files where
    possible — do not retype them.

11. **Integrations with other systems** — every external dependency the system reads from,
    writes to, or coordinates with. Stripe, SendGrid, S3, third-party CRMs, sister
    services in other repos. Read SDK initialization code, env-var lists, credential
    config. For each integration: purpose, direction (consumer / producer / both),
    authentication method, failure mode, what owns the contract (us or them).

12. **Operations** — how to run the system locally, how it's deployed to production,
    where logs and metrics live, the on-call runbook for the top 3 alerts. Read CI
    configs, Dockerfiles, deployment scripts, observability config, existing runbooks.

13. **Glossary** — domain terms used by the code that an outsider wouldn't know. Pull
    from class/table/event names. Three columns: term, definition, where it appears.

### Phase 3 — Index + cross-links

Write `docs/README.md` as the index. List every file with a one-line description.
Group by dimension category. Make sure every cross-reference in the dimension files
resolves to an actual file.

### Phase 4 — Review with the user

Present the punch list of files written (or, in refresh mode, files modified) and ask
the user to spot-check 2–3 sections of their choice. Iterate based on corrections.

## Constraints

- **Do not invent.** If the code doesn't show it, don't write it. Leave a `TODO:` with
  the question you'd need answered.
- **Do not paraphrase the code line-by-line.** Documentation explains *why* and *how it
  fits*, not *what each line does*. If your draft reads like a tour of every function,
  delete and start over with the dimension's actual purpose in mind.
- **Do not generate diagrams that don't help.** A Mermaid diagram is justified when the
  shape of the relationship is non-obvious from prose. Three boxes connected by one
  arrow is not a justified diagram.
- **Do not duplicate the README.** If the project has a top-level README, link to it from
  the system overview rather than restating it.
- **Do not commit your draft without the user reviewing it.** This skill produces files
  for the user; the user is the editor.
- **Do not assume CQRS / event-sourcing / hexagonal** are present unless the code shows
  they are. The Commands/Queries/Effects split in the dimension list is a useful
  *organization* of any codebase's behavior — most projects don't enforce strict CQRS,
  and the docs should reflect the actual code, not impose a paradigm.
- **In refresh mode, do not delete sections** the user wrote by hand. If your reading of
  the code conflicts with an existing doc claim, surface the conflict and ask — don't
  silently overwrite.

## References

- `references/output-skeleton.md` — recommended `docs/` directory layout, with one paragraph
  per file describing what goes in it. Read this in Phase 1 once you know the topology.
- `references/topology-detection.md` — heuristics for distinguishing single repo /
  monorepo / polyrepo and finding the right docs root. Read this in Phase 1 before
  asking the user.
