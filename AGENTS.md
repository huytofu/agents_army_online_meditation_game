# Cloud agent notes

Read only the assigned phase file in `docs/plans/`. Use `docs/plans/00-master-plan.md` for the shared design. When the master plan and a phase file disagree, follow the phase file.

Start Docker before database tests:

```bash
docker compose up -d
```

On Linux, activate the virtualenv with `source .venv/bin/activate`. Do not replace Postgres with SQLite.
