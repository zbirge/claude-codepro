# /save-session - Save Session State

Save current session state for later continuation with `ccp --continue`.

## When to Use

Use this command when you want to:
- Exit Claude Code temporarily to do other work
- Save detailed context about your current task
- Ensure smooth continuation later

## Instructions

Write a detailed continuation file to `/tmp/claude-continuation.md` using this format:

```markdown
# Session Continuation

**Task:** [Brief description of what you were working on]

**Files Modified:**
- `path/to/file1.py` - [what was changed]
- `path/to/file2.py` - [what was changed]

**Completed:**
- [x] [What was finished]
- [x] [Another completed item]

**In Progress:**
- [ ] [Current task being worked on]

**Next Steps:**
1. [IMMEDIATE: First thing to do when resuming]
2. [THEN: Second action]
3. [FINALLY: Complete the work]

**Context:**
- [Key decisions made during this session]
- [Any blockers or issues encountered]
- [User preferences to remember]
```

After writing the file, confirm:

```
Session saved to /tmp/claude-continuation.md

To resume later:
1. Exit Claude Code (Ctrl+C or type 'exit')
2. Run: ccp --continue

Your session context will be restored automatically.
```

## Notes

- The file at `/tmp/claude-continuation.md` is also written automatically on normal exit, but with less detail
- This manual save captures more specific context about your work
- Claude Mem also captures session observations as backup
