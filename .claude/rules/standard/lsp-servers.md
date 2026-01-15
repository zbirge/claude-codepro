## LSP Servers - Code Intelligence (USE PROACTIVELY!)

**⚠️ CRITICAL: Use LSP tools BEFORE grep/search for code understanding. LSP provides compiler-accurate results that grep cannot match.**

**Available:** Python (Pyright), TypeScript

### MANDATORY LSP Usage

**You MUST use LSP in these situations:**

| Situation | LSP Operation | Why NOT grep |
|-----------|---------------|--------------|
| Finding unused functions | `findReferences` | Grep misses dynamic calls, LSP knows all usages |
| Checking who calls a function | `findReferences` or `incomingCalls` | Grep finds text matches, not actual calls |
| Understanding function signature | `hover` | Grep can't infer types |
| Listing all functions in file | `documentSymbol` | More accurate than regex patterns |
| Before deleting/renaming | `findReferences` | Ensures you don't break callers |
| Tracing call chains | `incomingCalls`/`outgoingCalls` | Grep cannot follow call graphs |

### Operations

| Operation | Use Case | Support |
|-----------|----------|---------|
| `goToDefinition` | Find where symbol is defined | ✅ Both |
| `findReferences` | Find all usages of a symbol | ✅ Both |
| `hover` | Get type info and documentation | ✅ Both |
| `documentSymbol` | List all symbols in a file | ✅ Both |
| `workspaceSymbol` | Search symbols across codebase | TS only |
| `prepareCallHierarchy` | Get call hierarchy item at position | ✅ Python |
| `incomingCalls` | Find callers of a function | ✅ Python |
| `outgoingCalls` | Find functions called by a function | ✅ Python |

### Required Parameters

All operations require: `filePath`, `line` (1-based), `character` (1-based)

### Common Workflows

**Finding unused code:**
```
1. LSP(documentSymbol, "file.py", 1, 1)     # List all functions
2. For each function:
   LSP(findReferences, "file.py", line, col) # Check if used
3. If only 1 reference (the definition) → UNUSED
```

**Safe refactoring:**
```
1. LSP(findReferences, "file.py", line, col) # Find all usages
2. Review each usage location
3. Make changes knowing full impact
```

**Understanding unfamiliar code:**
```
1. LSP(documentSymbol, "file.py", 1, 1)      # Get structure overview
2. LSP(hover, "file.py", line, col)          # Get types and docs
3. LSP(outgoingCalls, "file.py", line, col)  # See what it calls
```

### Examples

```
# Get function signature and docs
LSP(hover, "installer/cli.py", 31, 5)

# Find all usages before renaming
LSP(findReferences, "installer/context.py", 15, 7)

# Understand what a function calls
LSP(outgoingCalls, "installer/cli.py", 31, 5)

# List all functions in a file
LSP(documentSymbol, "installer/ui.py", 1, 1)

# Find who calls this function
LSP(incomingCalls, "installer/cli.py", 31, 5)
```

### When Grep is OK

Only use grep/Glob when:
- Searching for string literals or comments
- Finding files by name pattern
- Looking for TODO/FIXME markers
- Searching across non-code files (markdown, config)

**For actual code understanding: LSP FIRST, grep as fallback.**
