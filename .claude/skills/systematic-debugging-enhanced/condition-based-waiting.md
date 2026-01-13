# Condition-Based Waiting

> **Attribution:** Adapted from [obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent.
> Licensed under MIT License. Copyright 2025 Jesse Vincent.

## Overview

Flaky tests often guess at timing with arbitrary delays. This creates race conditions where tests pass on fast machines but fail under load or in CI.

**Core principle:** Wait for the actual condition you care about, not a guess about how long it takes.

## When to Use

**Use when:**
- Tests have arbitrary delays (`setTimeout`, `sleep`, `time.sleep()`)
- Tests are flaky (pass sometimes, fail under load)
- Tests timeout when run in parallel
- Waiting for async operations to complete

**Don't use when:**
- Testing actual timing behavior (debounce, throttle intervals)
- Always document WHY if using arbitrary timeout

## Core Pattern

```typescript
// BAD: Guessing at timing
await new Promise(r => setTimeout(r, 50));
const result = getResult();
expect(result).toBeDefined();

// GOOD: Waiting for condition
await waitFor(() => getResult() !== undefined);
const result = getResult();
expect(result).toBeDefined();
```

## Quick Patterns

| Scenario | Pattern |
|----------|---------|
| Wait for event | `waitFor(() => events.find(e => e.type === 'DONE'))` |
| Wait for state | `waitFor(() => machine.state === 'ready')` |
| Wait for count | `waitFor(() => items.length >= 5)` |
| Wait for file | `waitFor(() => fs.existsSync(path))` |
| Complex condition | `waitFor(() => obj.ready && obj.value > 10)` |

## Implementation

Generic polling function:

```typescript
async function waitFor<T>(
  condition: () => T | undefined | null | false,
  description: string,
  timeoutMs = 5000
): Promise<T> {
  const startTime = Date.now();

  while (true) {
    const result = condition();
    if (result) return result;

    if (Date.now() - startTime > timeoutMs) {
      throw new Error(`Timeout waiting for ${description} after ${timeoutMs}ms`);
    }

    await new Promise(r => setTimeout(r, 10)); // Poll every 10ms
  }
}
```

**Python version:**

```python
import time

def wait_for(condition, description, timeout_s=5.0):
    start = time.time()
    while True:
        result = condition()
        if result:
            return result
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Timeout waiting for {description} after {timeout_s}s")
        time.sleep(0.01)  # Poll every 10ms
```

## Common Mistakes

**Polling too fast:**
```typescript
// BAD: setTimeout(check, 1) - wastes CPU
// GOOD: Poll every 10ms
await new Promise(r => setTimeout(r, 10));
```

**No timeout:**
```typescript
// BAD: Loop forever if condition never met
while (!condition()) { await sleep(10); }

// GOOD: Always include timeout with clear error
if (Date.now() - start > timeout) {
  throw new Error(`Timeout: ${description}`);
}
```

**Stale data:**
```typescript
// BAD: Cache state before loop
const state = getState();
while (state !== 'ready') { ... }

// GOOD: Call getter inside loop for fresh data
while (getState() !== 'ready') { ... }
```

## When Arbitrary Timeout IS Correct

```typescript
// Tool ticks every 100ms - need 2 ticks to verify partial output
await waitForEvent(manager, 'TOOL_STARTED'); // First: wait for condition
await new Promise(r => setTimeout(r, 200));   // Then: wait for timed behavior
// 200ms = 2 ticks at 100ms intervals - documented and justified
```

**Requirements:**
1. First wait for triggering condition
2. Based on known timing (not guessing)
3. Comment explaining WHY

## Real-World Impact

From debugging sessions:
- Fixed 15 flaky tests across 3 files
- Pass rate: 60% → 100%
- Execution time: 40% faster
- No more race conditions

## Quick Reference

| Problem | Solution |
|---------|----------|
| Flaky test with sleep | Replace with `waitFor()` |
| Race condition | Wait for actual state change |
| CI-only failures | Condition-based, not time-based |
| Slow tests | Condition resolves faster than worst-case timeout |
