# my-agent-skills

Personal collection of [Agent Skills](https://agentskills.io) — portable `SKILL.md` folders
that work with GitHub Copilot (VS Code agent mode, Copilot CLI, cloud coding agent) and
Claude (Claude Code / claude.ai).

## Skills

| Skill | What it does |
|---|---|
| `design-image-to-yaml` | Turn a mockup/screenshot into a dev-ready YAML spec: semantic HTML tree, CSS classes/styles, measured hex colors, fonts, verbatim copy. |

## Install on a machine (personal skills — available in every repo)

```bash
git clone <this-repo> ~/my-agent-skills
~/my-agent-skills/install.sh          # symlinks every skill into ~/.copilot/skills and ~/.claude/skills
```

`git pull` in `~/my-agent-skills` later picks up updates automatically because they are symlinks.

## Install into one project (shared with the whole team via the repo)

```bash
# from inside the project repo
mkdir -p .github/skills
cp -r ~/my-agent-skills/skills/design-image-to-yaml .github/skills/
git add .github/skills && git commit -m "Add design-image-to-yaml agent skill"
```

Copilot also reads `.claude/skills/` and `.agents/skills/`; `.github/skills/` is the
conventional location for Copilot-first teams.

## Using it

In VS Code Copilot Chat (agent mode) or Copilot CLI, attach the image and ask, e.g.:

> Turn this mockup into a YAML spec for the team using the design-image-to-yaml skill.

Copilot picks the skill up from its `description` even without naming it. The palette
and validator scripts need Python 3 with `pillow` and `pyyaml`:

```bash
pip install pillow pyyaml
```

## Adding a skill

Create `skills/<name>/SKILL.md` with `name` and `description` frontmatter (lowercase,
hyphens), put helpers under `scripts/` and docs under `references/`, then re-run
`install.sh`.
