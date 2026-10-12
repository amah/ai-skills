---
name: plantuml
description: |
  Use when the user asks to create, modify, explain, or troubleshoot PlantUML diagrams
  or .puml files, including sequence, class, activity, component, state, deployment,
  and use-case diagrams. Follow official PlantUML syntax and validate when tooling exists.
version: 0.1.0
targets: [claude, opencode]
tags: [diagrams, documentation]
---

# plantuml

Create and maintain readable, correct PlantUML diagrams as text-based source files.

## When to apply

- The user requests a PlantUML diagram or a `.puml` / `.plantuml` file.
- The user wants to translate architecture, workflows, or interactions into a diagram.
- The user needs to update, explain, or debug existing PlantUML source.

## Procedure

1. Identify the diagram type from the task: sequence for interactions, class for structure, activity for workflows, component for dependencies, deployment for runtime topology, state for transitions, or use-case for actors and goals. Ask only when ambiguity changes the result materially.
2. Inspect any existing `.puml` files and preserve the project's naming, styling, includes, and conventions.
3. Write minimal, legible PlantUML source bounded by `@startuml` and `@enduml`. Prefer stable identifiers, descriptive labels, and small coherent diagrams.
4. Use only relationships, actors, components, and transitions supported by the user's information. Clearly label assumptions rather than inventing system facts.
5. Check syntax against the bundled offline references in `references/` for the selected diagram type; consult the official website only when network access is available and needed. When a local PlantUML CLI or compatible renderer is available, render the diagram and resolve errors; otherwise say validation was not run.
6. Return the `.puml` source or update the requested file, and briefly explain non-obvious modeling choices.

## Constraints

- Do not claim a diagram rendered or passed validation unless it actually did.
- Do not paste untrusted remote `!include` directives or invoke external resources without checking project policy and user intent.
- Avoid embedding credentials, personal data, or sensitive production identifiers in diagram text.
- Keep source editable; do not replace requested PlantUML source with an image.
- Prefer official syntax and documentation over guessed keywords.

## Official documentation

- Language guide: https://plantuml.com/
- Sequence diagrams: https://plantuml.com/sequence-diagram
- Class diagrams: https://plantuml.com/class-diagram
- Activity diagrams: https://plantuml.com/activity-diagram-beta
- Component diagrams: https://plantuml.com/component-diagram
- Deployment diagrams: https://plantuml.com/deployment-diagram
- State diagrams: https://plantuml.com/state-diagram
- Use-case diagrams: https://plantuml.com/use-case-diagram
- Command line: https://plantuml.com/command-line

## Examples

- [Diagram examples](references/diagram-examples.md) — load this reference to select and adapt an editable `.puml` example for each supported diagram type.

## Offline documentation

- [Offline authoring guide](references/offline-guide.md) — file format, styling, preprocessing, rendering, troubleshooting, and safety.
- [Sequence syntax](references/sequence-syntax.md)
- [Class syntax](references/class-syntax.md)
- [Activity syntax](references/activity-syntax.md)
- [Component syntax](references/component-syntax.md)
- [Deployment syntax](references/deployment-syntax.md)
- [State syntax](references/state-syntax.md)
- [Use-case syntax](references/use-case-syntax.md)

Use these bundled files first. External documentation links are supplementary and are not required for the covered workflows.

- [Stereotypes](references/stereotypes.md) — UML extension labels, diagram-specific usage, naming conventions, and styling.
