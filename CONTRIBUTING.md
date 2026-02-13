# Contributing

Thanks for considering contributing!

## Dev setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Adding a new skill

1. Copy the template:
   - `.agents/skills/skill-template/` -> `.agents/skills/<your-skill-name>/`
2. Update frontmatter:
   - `name` must match folder name
   - `description` must include trigger keywords
3. Make output contract **JSON-only**
4. Run:
   - `solo-company skills validate`
   - `pytest`

## Pull request checklist

- [ ] Code is readable
- [ ] Tests added/updated
- [ ] Docs updated if needed
- [ ] `solo-company run ... --provider mock` still works
