# Evidence: architecture

For how a system fits together: services, modules, data flow, deployment. The evidence is the system's real structure and one real flow traced through it.

## Chapters are flows, not files

Organise chapters around questions the learner must answer about the system ("what happens when a user places an order", "how a model reaches production"). A flow chapter sets `file=None` and each step names the file it shows: `ST("s2", "...", "...", span, subs, file="services/orders/handler.py")`.

## Structure, derived from the real system

Diagrams come from the system's own definitions, so they cannot drift from it:

- Services and dependencies: parse `docker-compose.yml`, Kubernetes manifests, Terraform, or the CI pipeline file.
- Module dependencies: parse imports (`ast` for Python, the bundler's module graph for JS).
- Data model: query the scratch database's `information_schema` or the ORM's metadata.

Render the structure as an SVG (Graphviz `dot -Tsvg` when installed, otherwise a generated SVG) into the tools folder and show it with `IMG`. Put the extraction script in the capture so the diagram is regenerated with the evidence.

## A flow, traced for real

Run the system (or the relevant part) on scratch infrastructure, send one real input, and capture what each component received and emitted: HTTP calls, queue messages, database writes, log lines, with their order and timestamps. One step per hop; the text explains why the boundary is there.

## Decisions

For each architectural decision the code embodies, a segment with: the constraint that forced it, the alternatives, the evidence that it works (a measurement, a failure it prevents), and its cost. Tag it as a design choice; these make the strongest interview material.
