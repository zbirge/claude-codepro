# Syncing with Upstream Repository

This fork (zbirge/claude-codepro) is based on [maxritter/claude-codepro](https://github.com/maxritter/claude-codepro).

## Quick Sync Commands

```bash
# Fetch latest upstream changes
git fetch upstream

# Merge upstream into main
git checkout main
git merge upstream/main

# Resolve conflicts, then commit
git add .
git commit -m "feat: sync with upstream maxritter/claude-codepro vX.X.X"
git push origin main
```

## Detailed Sync Process

### 1. Prerequisites

Ensure the upstream remote is configured:

```bash
# Check remotes
git remote -v

# If upstream is missing, add it
git remote add upstream https://github.com/maxritter/claude-codepro.git
```

### 2. Fetch Upstream Changes

```bash
git fetch upstream
```

### 3. Check for Conflicts (Optional Preview)

Before merging, you can preview potential conflicts:

```bash
# See commits that will be merged
git log main..upstream/main --oneline

# See file differences
git diff main..upstream/main --stat
```

### 4. Execute the Merge

```bash
git checkout main
git merge upstream/main
```

If there are no conflicts, the merge will complete automatically.

### 5. Resolve Conflicts

When conflicts occur, Git will list the conflicting files. For each file:

1. Open the file and look for conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
2. Decide which changes to keep (or combine both)
3. Remove the conflict markers
4. Stage the resolved file: `git add <file>`

**Common Conflict Patterns in This Fork:**

| File Type | Strategy |
|-----------|----------|
| Version files (`__init__.py`, `install.sh`) | Use new version (e.g., 4.6.0) |
| Config files (`.claude/settings.local.json`) | Keep fork customizations, add upstream features |
| Installer steps | Keep fork features (GitHub/GitLab MCP), add upstream features |
| Documentation | Merge content, update version references |
| `.vscode/settings.json` | Keep fork version (use `git checkout --ours`) |

### 6. Update Version Numbers

After resolving conflicts, ensure all version references are updated:

```bash
# Search for old version references
grep -r "v4\.[0-9]" --include="*.py" --include="*.sh" --include="*.md" --include="*.tsx" --include="*.json" .

# Files to update:
# - installer/__init__.py: __version__ = "X.X.X"
# - install.sh: VERSION="X.X.X"
# - README.md: version URLs
# - .devcontainer/devcontainer.json: version URLs
# - docs/site/src/components/HeroSection.tsx: version URLs
# - docs/site/src/components/InstallSection.tsx: version URLs
```

### 7. Run Tests

```bash
# Run test suite
uv run pytest

# Check linting
ruff check .

# Type checking
basedpyright installer
```

### 8. Commit and Push

```bash
git commit -m "$(cat <<'EOF'
feat: sync with upstream maxritter/claude-codepro vX.X.X

Merge upstream improvements while preserving fork customizations:
- [List upstream features added]
- [List fork features preserved]

Version bumped to X.X.X

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"

git push origin main
```

## Fork-Specific Features

This fork maintains the following customizations that should be preserved during syncs:

- **GitHub MCP Server Integration** (`installer/steps/dependencies.py`)
- **GitLab MCP Server Integration** (`installer/steps/dependencies.py`)
- **OAuth Token Support** for Claude Code authentication
- **Superpowers Skills** (`.claude/skills/`)
- **VS Code Settings** (`.vscode/settings.json`)
  - `"workbench.iconTheme": "material-icon-theme"` - Material icons theme
  - `"workbench.colorTheme": "GitHub Dark Dimmed"` - GitHub dark theme
  - Removed upstream settings: `outline.collapseItems`, `workbench.activityBar.location`, `workbench.sideBar.location`, `workbench.panel.defaultLocation`

## Fork-Specific CI/CD Differences

This fork has the following CI/CD differences from upstream:

| Workflow | Difference | Reason |
|----------|------------|--------|
| `release.yml` | Removed `deploy-website` job | Fork does not use Netlify hosting |

**During syncs:** If upstream modifies the release workflow, verify the `deploy-website` job (Netlify deployment) is not re-added. If it is, remove it again.

## Version Numbering Strategy

This fork uses version numbers ahead of upstream to avoid confusion:

| Upstream Version | Fork Version |
|------------------|--------------|
| 4.3.4 | 4.5.0 |
| 4.4.6 | 4.6.0 |
| 4.5.x | 4.7.x |
| 4.6.x | 4.8.x |

When syncing, bump the fork version to stay ahead of the upstream version being merged.

## Troubleshooting

### Merge Conflicts in Test Files

Test files often conflict when both repos add tests. Strategy:
- Keep both sets of tests
- Update mock decorators to include any new dependencies
- Ensure test input matches the new prompt flow

### License Prompt Breaking Tests

If tests fail due to license prompts:
- Add `--non-interactive` flag to test commands, OR
- Mock `load_config` to return `{"license_acknowledged": True}`

### Step Count Changed

If `test_get_all_steps_returns_list` fails:
- Count steps in `installer/cli.py:get_all_steps()`
- Update the expected count in the test

## Sync History

| Date | Upstream Version | Fork Version | Notes |
|------|------------------|--------------|-------|
| 2026-01-15 | 4.4.6 | 4.6.0 | Added macOS builds, preserved GitHub/GitLab MCP |
| 2026-01-14 | 4.3.4 | 4.5.0 | Initial documented sync |
