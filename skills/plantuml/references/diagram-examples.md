# PlantUML diagram examples

These editable examples use a fictional online ordering platform. Select the file matching the user's modeling task and adapt entities and relationships to real requirements; do not assume the example architecture matches the user's system.

| Diagram | File | Purpose | Official guide |
| --- | --- | --- | --- |
| Sequence | [sequence.puml](../examples/sequence.puml) | Order/payment message exchange | https://plantuml.com/sequence-diagram |
| Class | [class.puml](../examples/class.puml) | Domain classes and multiplicities | https://plantuml.com/class-diagram |
| Activity | [activity.puml](../examples/activity.puml) | Checkout workflow and decision | https://plantuml.com/activity-diagram-beta |
| Component | [component.puml](../examples/component.puml) | Logical application dependencies | https://plantuml.com/component-diagram |
| Deployment | [deployment.puml](../examples/deployment.puml) | Runtime nodes and connections | https://plantuml.com/deployment-diagram |
| State | [state.puml](../examples/state.puml) | Order lifecycle transitions | https://plantuml.com/state-diagram |
| Use-case | [use-case.puml](../examples/use-case.puml) | Actors and platform goals | https://plantuml.com/use-case-diagram |

To render locally when PlantUML is installed, run `plantuml -tsvg examples/*.puml` from the skill directory. This generates SVGs next to the sources. The examples are illustrative, not a specification of any production system.
