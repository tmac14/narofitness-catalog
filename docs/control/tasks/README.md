# Task Packets

Task packets preserve rich, task-specific context independently of chat
history.

## Rules

- One packet per non-trivial implementation, audit, QA, validation, or
  coordination task.
- File name equals the task ID: `<TASK-ID>.md`.
- Create the packet during discovery, before implementation.
- Update it after plan approval, implementation, validation, block, pause, or
  closure.
- Keep summaries concise; link durable evidence instead of copying reports.
- Task status and dependencies must match `TASK_REGISTRY.yaml`.
- Closed packets remain immutable except for explicit corrections or links to
  superseding decisions.

Use `TASK_PACKET_TEMPLATE.md` for new tasks.
