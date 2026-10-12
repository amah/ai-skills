# Component diagram syntax

Model logical modules, interfaces and dependencies, not physical machines.

```plantuml
@startuml
skinparam componentStyle rectangle
package "Ordering" {
  [Web UI] as Web
  component "Order API" as API
  interface "Payments" as Payments
}
database "Orders DB" as DB
Web --> API : HTTPS
API --> DB : SQL
API ..> Payments : requires
@enduml
```

## Elements

`component "Label" as Alias` or `[Label] as Alias` defines a component. `interface` declares a service contract. `package`, `node`, `folder`, `frame`, and `cloud` may group elements as appropriate. Connect with `--`, `-->`, `..>`, and labeled arrows. `left to right direction` can improve orientation.

## Modeling rules

Distinguish provided interfaces from required dependencies. Name protocols only when known. Prefer explicit arrows over ambiguous unlabeled lines. Use deployment diagrams for physical hosts and class diagrams for internal domain types.
