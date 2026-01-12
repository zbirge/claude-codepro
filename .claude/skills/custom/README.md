# Custom Skills Guide

This directory contains project-specific skills that are **preserved during installation updates**.

## Directory Structure

```
.claude/skills/
├── custom/                    # YOUR SKILLS (preserved)
│   ├── README.md              # This file
│   ├── project-*/             # Project workflows
│   ├── team-*/                # Team collaboration
│   └── domain-*/              # Domain expertise
└── [standard skills]          # Framework skills (managed by installer)
```

## Naming Conventions

Use prefixed names to organize skills by category:

| Prefix | Use For | Examples |
|--------|---------|----------|
| `project-` | Project-specific workflows | `project-deploy`, `project-build` |
| `team-` | Team collaboration | `team-review`, `team-standup` |
| `domain-` | Domain expertise | `domain-security`, `domain-api-design` |
| `workflow-` | Multi-step processes | `workflow-release`, `workflow-incident` |

## Creating a Custom Skill

### 1. Create the skill directory

```bash
mkdir -p .claude/skills/custom/project-deploy
```

### 2. Create SKILL.md

```bash
touch .claude/skills/custom/project-deploy/SKILL.md
```

### 3. Define the skill content

```markdown
# Project Deploy

Deploy the application to the specified environment.

## Arguments

- `env`: Target environment (staging, production)

## Steps

1. Run tests: `npm test`
2. Build: `npm run build`
3. Deploy: `npm run deploy:${env}`

## Safety Checks

- [ ] All tests pass
- [ ] No uncommitted changes
- [ ] Branch is up to date with main
```

## Skill File Format

Each skill needs a `SKILL.md` file with:

```markdown
# Skill Name

Brief description of what the skill does.

## Arguments (optional)

List any parameters the skill accepts.

## Steps

Detailed instructions for Claude to follow.

## Examples (optional)

Show example usage or expected outputs.
```

## Best Practices

### Do

- Use clear, descriptive names
- Include step-by-step instructions
- Add safety checks for destructive operations
- Document any prerequisites

### Don't

- Use nested subdirectories (not supported by Claude Code)
- Include sensitive data (API keys, passwords)
- Create overly complex single skills (split into multiple)

## Why Custom Skills Are Preserved

The installer clears standard skills during updates but **never touches** `skills/custom/`:

- Fresh install: `skills/custom/` is created with `.gitkeep`
- Update/reinstall: Only non-custom skills are cleared
- Your custom skills are safe!

## Invoking Skills

Custom skills are invoked by name:

```
/project-deploy
/team-review
/domain-security
```

Or reference them in conversation:
> "Run the project-deploy skill with env=staging"

## Git Tracking

Custom skills are tracked in your project's git repository:

```bash
git add .claude/skills/custom/
git commit -m "feat: add project-deploy skill"
```

## Limitations

- **No nested directories**: Claude Code only searches one level deep
- **Workaround**: Use naming prefixes instead (e.g., `team-review`, `team-standup`)
- **Issue tracking**: [GitHub Issue #10238](https://github.com/anthropics/claude-code/issues/10238)

## Template: Quick Start

Copy this template to create a new skill:

```bash
# Create skill directory
mkdir -p .claude/skills/custom/my-skill

# Create SKILL.md with template
cat > .claude/skills/custom/my-skill/SKILL.md << 'EOF'
# My Skill

Brief description.

## Arguments

- `arg1`: Description

## Steps

1. First step
2. Second step
3. Third step

## Example

```
/my-skill arg1=value
```
EOF
```
