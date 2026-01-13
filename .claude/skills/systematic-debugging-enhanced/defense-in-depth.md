# Defense-in-Depth Validation

> **Attribution:** Adapted from [obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent.
> Licensed under MIT License. Copyright 2025 Jesse Vincent.

## Overview

When you fix a bug caused by invalid data, adding validation at one place feels sufficient. But that single check can be bypassed by different code paths, refactoring, or mocks.

**Core principle:** Validate at EVERY layer data passes through. Make the bug structurally impossible.

## Why Multiple Layers Matter

| Approach | Result |
|----------|--------|
| Single validation | Bug is "fixed" but can recur |
| Multiple layers | Bug is structurally impossible |

Different validation points serve distinct purposes:
- **Entry validation** intercepts most invalid inputs
- **Business logic validation** ensures operational soundness
- **Environment guards** protect against context-specific risks
- **Debug instrumentation** provides forensic information when other safeguards fail

## The Four-Layer Approach

### Layer 1: Entry Point Validation

Examine inputs at API boundaries, reject obviously problematic data before processing begins.

```typescript
function createProject(name: string, directory: string) {
  if (!directory || directory.trim() === '') {
    throw new Error('Directory cannot be empty');
  }
  // Continue with valid data
}
```

### Layer 2: Business Logic Validation

Verify data appropriateness for specific operations within business logic.

```typescript
class WorkspaceManager {
  async initialize(projectDir: string) {
    if (!path.isAbsolute(projectDir)) {
      throw new Error('Project directory must be absolute path');
    }
    // Continue with valid path
  }
}
```

### Layer 3: Environment Guards

Implement context-aware guards, such as restricting dangerous file operations during testing.

```typescript
async function gitInit(directory: string) {
  if (process.env.NODE_ENV === 'test') {
    const tmpDir = os.tmpdir();
    if (!directory.startsWith(tmpDir)) {
      throw new Error(`Refusing to git init outside tmpdir in test mode: ${directory}`);
    }
  }
  await execFileAsync('git', ['init'], { cwd: directory });
}
```

### Layer 4: Debug Instrumentation

Add logging and stack traces for debugging when earlier layers fail.

```typescript
async function gitInit(directory: string) {
  console.error('DEBUG git init:', {
    directory,
    cwd: process.cwd(),
    nodeEnv: process.env.NODE_ENV,
    stack: new Error().stack,
  });
  // Proceed with operation
}
```

## Implementation Strategy

When encountering bugs:

1. **Trace** how corrupted data flows through systems
2. **Identify** all validation checkpoints (entry, logic, env, debug)
3. **Add checks** at each layer
4. **Test** that bypassing one layer still results in failure at another

## Why All Four Layers?

From real debugging sessions, all four layers proved necessary:
- Different code paths bypassed Layer 1
- Mocks bypassed Layer 2
- Platform variations bypassed Layer 3
- Layer 4 caught what others missed

**No single layer is sufficient.** Each serves a purpose and catches what others miss.

## Quick Reference

| Layer | Purpose | Example Check |
|-------|---------|---------------|
| 1. Entry | Block bad input | `if (!dir) throw` |
| 2. Logic | Business rules | `if (!path.isAbsolute(dir)) throw` |
| 3. Environment | Context safety | `if (test && !inTmpdir) throw` |
| 4. Debug | Forensics | `console.error({ dir, stack })` |

## When to Apply

Apply defense-in-depth after finding ANY root cause:

1. You've traced back to the source
2. You've fixed the source
3. Now add validation at EVERY layer the bad data passed through
4. Future bugs of this class are now structurally impossible
