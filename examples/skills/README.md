# Claude Code Skills

These are [Claude Code](https://claude.ai/code) skills that use `pms` to give Claude the ability to search and analyse Polymarket markets.

## Installation

Copy the skill file into your project's `.claude/commands/` directory (create it if it doesn't exist):

```bash
mkdir -p .claude/commands
cp polymarket-analysis.md .claude/commands/
```

Then invoke it from Claude Code:

```
/polymarket-analysis will the Fed cut rates this year
```

## Skills

| Skill | Description |
|-------|-------------|
| `polymarket-analysis` | Search for markets on a topic, pull live prices, and summarise the crowd's view |
