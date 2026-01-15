## Library Documentation with Context7

**MANDATORY: Use Context7 BEFORE writing code with unfamiliar libraries.** Context7 provides up-to-date documentation, code examples, and best practices that prevent mistakes and save time.

### When to Use Context7 (Proactively!)

| Situation | Action |
|-----------|--------|
| Adding new dependency | Query Context7 for setup and usage patterns |
| Using library for first time | Query Context7 for API overview and examples |
| Implementing specific feature | Query Context7 for that feature's documentation |
| Getting errors from a library | Query Context7 for correct usage patterns |
| Unsure about library capabilities | Query Context7 to understand what's available |

**Don't guess or assume** - Context7 has 1000s of indexed libraries with real documentation.

### Workflow

```
# Step 1: Get library ID
resolve-library-id(query="your question", libraryName="package-name")
→ Returns libraryId (e.g., "/npm/react")

# Step 2: Query docs (can call multiple times with different queries)
query-docs(libraryId="/npm/react", query="specific question")
→ Returns relevant documentation with code examples
```

### Query Tips

Use descriptive queries - they drive result relevance:
- ❌ `"fixtures"` → ✅ `"how to create and use fixtures in pytest"`
- ❌ `"hooks"` → ✅ `"useState and useEffect patterns in React"`
- ❌ `"auth"` → ✅ `"how to implement JWT authentication with refresh tokens"`

**Multiple queries are encouraged** - each query can reveal different aspects of the library.

### Tool Selection Guide

| Need | Primary Tool | Fallback |
|------|--------------|----------|
| Library API reference | Context7 | Official docs |
| Framework patterns | Context7 | Official docs |
| Code examples | Context7 | GitHub search |
| Error message lookup | WebSearch | Stack Overflow |
| General web research | WebSearch | - |
| Codebase patterns | Vexor | Grep/Glob |

### Example: Learning a New Library

When asked to use `claude-agent-sdk` for the first time:

```
# 1. Resolve the library
resolve-library-id(query="programmatic queries with Claude Agent SDK", libraryName="claude-agent-sdk")
→ /anthropics/claude-agent-sdk-python

# 2. Query for overview
query-docs(libraryId="/anthropics/claude-agent-sdk-python", query="complete overview features capabilities installation")

# 3. Query for specific use case
query-docs(libraryId="/anthropics/claude-agent-sdk-python", query="structured JSON output with schema validation")

# 4. Query for authentication/setup
query-docs(libraryId="/anthropics/claude-agent-sdk-python", query="authentication setup API keys vs Claude Max")
```

### Troubleshooting

- **Library not found:** Try variations like `@types/react` vs `react`, or `node:fs` for built-ins
- **Poor results:** Make query more specific, describe what you're trying to accomplish
- **Empty results:** Library may not be indexed - check official docs directly
- **Multiple libraries found:** Check the benchmark score and code snippet count to pick the best one

### Key Principle

**Learn before you code.** Spending 30 seconds querying Context7 prevents hours of debugging from incorrect assumptions about library behavior.
