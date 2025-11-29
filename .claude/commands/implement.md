---
description: Execute implementation plans in batches with Claude CodePro
model: opus
---
# IMPLEMENT MODE: Task Execution with Mandatory Context Gathering

**Execute ALL tasks continuously. NO stopping unless context manager says context is full.**

## MCP Servers - Use Throughout Implementation

| Server | Purpose | When to Use |
|--------|---------|-------------|
| **Cipher** | Project memory | Query gotchas, store learnings after each task |
| **Claude Context** | Semantic code search | Find related code, verify patterns |
| **Exa** | Web search & code examples | Look up library APIs, find solutions |
| **MCP Funnel** | Tool discovery | Find specialized tools when stuck |

**Query Cipher at start and store learnings at end of each task.**


## Mandatory Context Gathering Phase (REQUIRED)

**Before ANY implementation, you MUST:**

1. **Read the COMPLETE plan** - Understanding overall architecture and design
2. **Verify comprehension** - Summarize what you learned to demonstrate understanding
3. **Identify dependencies** - List files, functions, classes that need modification
4. **Check current state:**
   - Git status: `git status --short` and `git diff --name-only`
   - Diagnostics: `mcp__ide__getDiagnostics()`
   - Plan progress: Check for `[x]` completed tasks
5. **Query knowledge base:**
   - Cipher: Past implementations and gotchas
   - Claude Context: Related patterns and components
   - Exa: External documentation if needed

## Per-Task Execution Flow

**For EVERY task, follow this exact sequence:**

1. **READ PLAN'S IMPLEMENTATION STEPS** - List all files to create/modify/delete
2. **Perform Call Chain Analysis:**
   - **Trace Upwards (Callers):** Identify what calls the code you're modifying
   - **Trace Downwards (Callees):** Identify what the modified code calls
   - **Side Effects:** Check for database, cache, external system impacts
3. **Mark task as in_progress** in TodoWrite
4. **Check diagnostics** - `mcp__ide__getDiagnostics()`
5. **Execute TDD Flow:**
   - Write failing test first (RED phase)
   - Implement minimal code to pass (GREEN phase)
   - Refactor if needed (REFACTOR phase)
6. **Verify tests pass** - `uv run pytest tests/path/to/test.py -v`
7. **Run actual program** - Show real output with sample data
8. **Check diagnostics again** - Must be zero errors
9. **Validate Definition of Done** - Check all criteria from plan
10. **Mark task completed** in TodoWrite
11. **Update plan file** - Change `[ ]` to `[x]`
12. **Check context usage**

## Critical Task Rules

**⚠️ NEVER SKIP TASKS:**
- EVERY task MUST be fully implemented
- NO exceptions for "MVP scope" or complexity
- If blocked: STOP and report specific blockers
- NEVER mark complete without doing the work

## Verification Checklist

Before marking complete:
- [ ] Test written and FAILED (RED phase)
- [ ] Implementation written
- [ ] Test PASSES (GREEN phase)
- [ ] Program executed with verified output
- [ ] No diagnostics errors

## When All Tasks Complete

1. Quick verification: `mcp__ide__getDiagnostics()` and `uv run pytest`
2. Store learnings in Cipher
3. Inform user: "✅ All tasks complete. Run `/verify`"
4. DO NOT run /verify yourself
