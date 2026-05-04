# Claude Code Skills

These are [Claude Code](https://claude.ai/code) skills that use `pms` to give Claude the ability to search and analyse Polymarket markets.

## Installation

**1. Install `pms`** so Claude can run it:

```bash
uv tool install polymarket-search
# or: pipx install polymarket-search
```

**2. Copy the skill** into your project's `.claude/commands/` directory:

```bash
mkdir -p .claude/commands
curl -o .claude/commands/polymarket-analysis.md \
  https://raw.githubusercontent.com/L-josh/polymarket-search/main/examples/skills/polymarket-analysis.md
```

**3. Invoke it** from Claude Code:

```
/polymarket-analysis will the Fed cut rates this year
```

## Skills

| Skill | Description |
|-------|-------------|
| `polymarket-analysis` | Search for markets on a topic, pull live prices, and summarise the crowd's view |
