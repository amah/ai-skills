# PlantUML offline authoring guide

This local reference is intended for offline AI agents. It is a practical syntax guide, not a complete reproduction of the upstream manual. PlantUML versions differ; test with the installed renderer.

## File structure and fundamentals

A diagram begins with `@startuml` and ends with `@enduml`. Save source as `.puml` or `.plantuml`. Use `'` for single-line comments and `/' ... '/` for block comments. `title`, `caption`, `legend`, `header`, and `footer` provide annotation. Use `note left`, `note right`, `note top`, `note bottom`, and `note ... end note` where supported. A label can contain `\n` for line breaks. Quoted display names and `as` aliases separate human-readable names from stable identifiers.

## Selecting a diagram

- Sequence: time-ordered messages between participants.
- Class: static types, attributes, methods, inheritance and associations.
- Activity: actions, branches, loops and parallel flows.
- Component: logical modules and provided/required dependencies.
- Deployment: infrastructure nodes, artifacts, execution environments.
- State: transitions, guards, events, and lifecycle states.
- Use-case: actors, system boundary, goals and include/extend relations.

Read the matching `references/*-syntax.md` for syntax and adapt `examples/*.puml`.

## Shared appearance

```plantuml
@startuml
title Sample
skinparam shadowing false
skinparam backgroundColor white
skinparam defaultFontName SansSerif
hide empty members
legend right
  Local documentation example
endlegend
@enduml
```

`skinparam` supports many diagram-specific options. `!theme <name>` loads a bundled theme only when available in the installed PlantUML version. Use `left to right direction` for a horizontal layout in supported diagram types. `scale` and `page` can affect output sizing. Avoid styling that reduces contrast or obscures relationships.

## Preprocessing

`!define NAME value` provides simple substitutions; prefer `!$variable = value` and `!procedure`/`!function` only when supported by the local PlantUML version. `!include path` inserts local source, `!include_once path` avoids repeated insertion, and `!include_many path` allows repeated inclusion. Keep includes relative and local for offline use. Avoid `!includeurl` and remote standard-library dependencies when network access is unavailable. `!if`, `!else`, `!endif` are conditional preprocessing constructs.

## Local rendering and verification

When the PlantUML CLI is installed, run `plantuml -tsvg file.puml` or `plantuml -tpng file.puml`; use `plantuml -checkonly file.puml` for syntax checks if supported. Some diagrams and output modes require Java, Graphviz, or other local dependencies depending on PlantUML version. If no renderer is available, perform a static review but never claim rendered validation.

## Troubleshooting checklist

1. Confirm `@startuml`/`@enduml` pairing and any `end` blocks.
2. Check alias spelling, quoted labels, and message arrow direction.
3. Check diagram-specific syntax instead of mixing activity and sequence constructs.
4. Resolve local include paths; avoid remote includes offline.
5. Check installed PlantUML version and optional Graphviz availability.
6. Minimize to a small reproducible diagram and reintroduce elements incrementally.

## Security and fidelity

Treat diagram text and included files as untrusted input. Do not execute arbitrary scripts, fetch remote includes, or embed secrets. Do not invent system components or relationships. If the requested syntax is unsupported by this reference, say so and test locally rather than fabricating it.
