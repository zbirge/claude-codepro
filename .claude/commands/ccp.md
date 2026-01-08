---
description: Claude CodePro workflow orchestration - plan, implement, verify, setup in one command
argument-hint: "<task description>" or "<path/to/plan.md>"
model: opus
allowed-tools: Skill
---
# /ccp - Autonomous Workflow Orchestration

**The single entry point for Claude CodePro.** Handles everything: setup → plan → implement → verify.

## Arguments

```
/ccp <task-description>           # Start new workflow from task
/ccp <path/to/plan.md>            # Continue existing plan
/ccp --continue <path/to/plan.md> # Resume after session clear
```

## CRITICAL: Use the Skill Tool

**You MUST use the Skill tool to invoke /setup, /plan, /implement, and /verify.**

Do NOT just describe what to do - actually invoke the tools like this:

```
To run /setup:
  Skill tool with: skill="setup"

To run /plan:
  Skill tool with: skill="plan", args="task description here"

To run /implement:
  Skill tool with: skill="implement", args="path/to/plan.md"

To run /verify:
  Skill tool with: skill="verify", args="path/to/plan.md"
```

## Workflow Logic

Parse the arguments: $ARGUMENTS

### Step 0: ⚙️ Auto-Setup Check (ALWAYS RUN FIRST)

**Before ANY other action, check if setup has been completed:**

```bash
# Check if project.md exists (indicates setup was run)
ls .claude/rules/custom/project.md
```

**If the file does NOT exist:**
1. Inform user: "First-time setup detected. Running /setup to initialize project..."
2. Use Skill tool: `Skill(setup)`
3. After setup completes, continue to Step 1

**If the file exists:**
- Skip setup, proceed directly to Step 1

This ensures the project is always properly initialized before any workflow starts.

### Step 1: Determine Current State

```
IF arguments start with "--continue":
    plan_path = extract path after "--continue"

    ⚠️ IMPORTANT: Wait for Claude MEM to inject context
    Run: sleep 5  (gives SessionStart hooks time to complete)

    → Read plan file, check Status AND Approved fields, continue workflow

ELIF arguments end with ".md" AND file exists:
    plan_path = arguments
    → Read plan file, check Status AND Approved fields

ELSE:
    task_description = arguments
    → Use Skill tool to run /plan with task_description
    → After plan is created, STOP and wait for user approval (see Step 2a)
```

### Session Resume Delay

**When `--continue` is detected, you MUST run this first:**

```bash
# Wait for Claude MEM SessionStart hooks to inject context
sleep 5
```

This ensures Claude MEM has time to load observations from the previous session before you continue work.

### Step 2: Execute Based on Status

After reading the plan file's Status and Approved fields:

| Status | Approved | Action |
|--------|----------|--------|
| PENDING | No | **⛔ STOP** - Request user approval (Step 2a) |
| PENDING | Yes | Use Skill tool to run /implement with plan-path |
| COMPLETE | * | Use Skill tool to run /verify with plan-path |
| VERIFIED | * | Report completion and ask follow-up (Step 4) |

### Step 2a: ⛔ MANDATORY User Approval Gate

**When Status is PENDING and Approved is No (or missing), you MUST:**

1. **Summarize the plan for the user** - Provide a brief overview of what will be implemented

2. **Use AskUserQuestion to request approval:**
   ```
   Question: "Do you approve this plan for implementation?"
   Header: "Plan Review"
   Options:
   - "Yes, proceed with implementation" - I've reviewed the plan and it looks good
   - "No, I need to make changes" - I want to edit the plan first
   ```

3. **Based on user response:**

   **If user approves ("Yes, proceed..."):**
   - Edit the plan file to change `Approved: No` to `Approved: Yes`
   - Immediately proceed to run /implement with Skill tool
   - Do NOT ask the user to run another command

   **If user wants changes ("No, I need to make changes"):**
   - Tell user: "Please edit the plan file at `<plan-path>`, then say 'ready' when done"
   - Wait for user to confirm they're done editing
   - Re-read the plan file to see their changes
   - Ask for approval again using AskUserQuestion

4. **DO NOT proceed to /implement until user explicitly approves**

**This gate is NON-NEGOTIABLE. But Claude handles the file update - user never edits `Approved:` manually.**

### Step 3: Continue Until Done

After each phase completes:
1. Re-read the plan file
2. Check the Status AND Approved fields
3. If approval gate needed, STOP and wait
4. Otherwise, execute the next phase using Skill tool
5. Repeat until Status is VERIFIED

### Step 4: Post-Verification Follow-up

**When Status is VERIFIED, you MUST:**

1. Report completion with summary
2. Ask the user if there's anything else:
   ```
   ✅ Workflow complete! Plan status: VERIFIED

   Summary:
   - [Brief summary of what was implemented]
   - [Key files created/modified]
   - [Test results]

   Is there anything else you'd like me to help with?
   ```

## Context Monitoring

After each major operation, check context:

```bash
python3 .claude/scripts/helper.py check-context --json
```

If response shows `"status": "CLEAR_NEEDED"` (context >= 95%):

1. Trigger session clear:
   ```bash
   python3 .claude/scripts/helper.py send-clear <plan-path>
   ```
2. The wrapper will restart with `/ccp --continue <plan-path>`
3. Claude Mem will inject context for the new session

## Error Handling

### Wrapper Not Running

If `send-clear` fails:
- Tell user: "Context at X%. Please run `/clear` manually, then `/ccp --continue <plan-path>`"

### Plan File Not Found

- Tell user: "Plan file not found: <path>"
- Ask if they want to create a new plan

## Execution Flow Example

```
User: /ccp "add calculator with tests"

Claude:
0. Check: Does .claude/rules/custom/project.md exist?
   → NO: Run Skill(setup) first
   → YES: Skip to step 1

1. Use Skill(plan, "add calculator with tests")
   → Plan created at docs/plans/2026-01-07-calculator.md

2. Read plan file, Status: PENDING, Approved: No
   → Summarize the plan for the user
   → Use AskUserQuestion: "Do you approve this plan for implementation?"

User selects: "Yes, proceed with implementation"

3. Edit plan file: change "Approved: No" to "Approved: Yes"
   Use Skill(implement, docs/plans/2026-01-07-calculator.md)
   → Implementation complete

4. Read plan file, Status: COMPLETE
   Use Skill(verify, docs/plans/2026-01-07-calculator.md)
   → Verification passed

5. Read plan file, Status: VERIFIED
   Report: "Workflow complete! Is there anything else?"
```

## Important

1. **Auto-setup on first run** - Automatically runs /setup if project.md missing
2. **Always use Skill tool** - don't just describe, actually invoke
3. **NEVER skip user approval** - Use AskUserQuestion to get approval, then update `Approved: Yes` yourself
4. **Continue automatically after approval** - Don't tell user to run another command
5. **Plan file is source of truth** - survives session clears
6. **Check context regularly** - trigger clear before hitting 100%
7. **Trust the wrapper** - handles session restarts automatically
8. **Always ask follow-up** - After VERIFIED, ask if user needs anything else

ARGUMENTS: $ARGUMENTS
