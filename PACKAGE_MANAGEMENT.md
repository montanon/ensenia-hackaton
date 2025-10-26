# 📦 Package Management Guide

This project uses **two package managers** for a hybrid Python + TypeScript application:

- 🐍 **Python**: `uv` (fast, modern)
- 📦 **TypeScript/JS**: `npm` (standard)

---

## Quick Start

```bash
# Install everything
./setup.sh

# Or manually:
uv sync                        # Python
cd app/worker && npm install   # Worker
```

---

## 1. Python Packages (uv)

### What is `uv`?

**uv** is a **super fast** Python package manager (100x faster than pip) by Astral (creators of Ruff).

### Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Configuration: `pyproject.toml`

```toml
[project]
name = "ensenia"
version = "0.1.0"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.0.0",
    "httpx>=0.25.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "ruff>=0.1.0",
]
```

### Common Commands

```bash
# Install all dependencies (creates .venv automatically)
uv sync

# Add a new dependency
uv add requests
uv add fastapi==0.104.0  # Specific version

# Add a dev dependency
uv add --dev pytest
uv add --dev ruff

# Remove a dependency
uv remove requests

# Update all packages
uv lock --upgrade

# Update a specific package
uv lock --upgrade-package fastapi

# Run a command in the virtual environment
uv run python -m app.ensenia.main
uv run pytest
uv run ruff check .

# Activate virtual environment manually (if needed)
source .venv/bin/activate  # Unix
.venv\Scripts\activate     # Windows

# Export to requirements.txt (for compatibility)
uv pip compile pyproject.toml -o requirements.txt
```

### Lock File: `uv.lock`

- **Auto-generated** by `uv sync`
- **DO NOT edit manually**
- **Commit to git** (ensures reproducible builds)
- Faster than traditional `requirements.txt`

### Virtual Environment: `.venv/`

- **Auto-created** by `uv sync`
- **DO NOT commit to git** (in `.gitignore`)
- Contains all installed packages

---

## 2. TypeScript/Node.js Packages (npm)

### Configuration: `app/worker/package.json`

```json
{
  "name": "ensenia-cloudflare-worker",
  "dependencies": {
    "@cloudflare/ai": "^1.0.59"
  },
  "devDependencies": {
    "@cloudflare/workers-types": "^4.20240208.0",
    "typescript": "^5.3.3",
    "wrangler": "^3.28.0"
  }
}
```

### Common Commands

```bash
# Install all dependencies
npm install

# Add a new dependency
npm install axios
npm install axios@1.6.0  # Specific version

# Add a dev dependency
npm install --save-dev @types/node

# Remove a package
npm uninstall axios

# Update all packages
npm update

# Update a specific package
npm update axios

# Check for outdated packages
npm outdated

# Run scripts
npm run dev
npm run deploy
npm test
```

### Lock File: `package-lock.json`

- **Auto-generated** by `npm install`
- **DO NOT edit manually**
- **COMMIT to git** (ensures reproducible builds)
- Locks exact versions of all dependencies

### Dependencies: `node_modules/`

- **Auto-created** by `npm install`
- **DO NOT commit to git** (in `.gitignore`)
- Contains all installed packages

---

## 3. Managing Both Together

### Option A: Root Scripts (package.json)

We created a **root `package.json`** with convenience scripts:

```bash
# Install everything
npm run install:all

# Install individually
npm run install:python
npm run install:worker

# Development
npm run dev:python     # Start FastAPI backend
npm run dev:worker     # Start CloudFlare Worker

# Testing
npm run test:python
npm run test:worker

# Cleanup
npm run clean
```

### Option B: Makefile

Use `make` commands (requires `make` installed):

```bash
# Install everything
make install

# Development
make dev-python
make dev-worker

# Testing
make test

# Cleanup
make clean
```

### Option C: Direct Commands

```bash
# Python
uv sync
uv run uvicorn app.ensenia.main:app --reload

# Worker
cd app/worker && npm install
cd app/worker && npm run dev
```

---

## 4. Project Structure

```
cloudflare/
├── pyproject.toml          # Python dependencies (uv)
├── uv.lock                 # Python lockfile (commit!)
├── .venv/                  # Python virtual env (ignore)
│
├── package.json            # Root scripts (optional)
├── Makefile                # Make commands (optional)
│
└── app/
    ├── ensenia/            # Python backend
    │   └── (Python code)
    │
    ├── web/                # React frontend (future)
    │   ├── package.json    # Web dependencies
    │   └── node_modules/   # Web deps (ignore)
    │
    └── worker/             # CloudFlare Worker
        ├── package.json    # Worker dependencies
        ├── package-lock.json  # Worker lockfile (commit!)
        └── node_modules/   # Worker deps (ignore)
```

---

## 5. Dependency Update Strategy

### Python (uv)

```bash
# Check what would be updated
uv lock --upgrade --dry-run

# Update all dependencies
uv lock --upgrade
uv sync

# Update specific package
uv lock --upgrade-package fastapi
uv sync

# Verify
uv run pytest
```

### Worker (npm)

```bash
cd app/worker

# Check outdated packages
npm outdated

# Update all minor/patch versions
npm update

# Update major versions (careful!)
npm install <package>@latest

# Verify
npm run type-check
npm test
```

### Best Practice

1. Update regularly (weekly/bi-weekly)
2. Test after updates
3. Commit lock files
4. Use semantic versioning constraints:
   - `>=1.0.0` - Allow all updates
   - `^1.0.0` - Allow minor/patch (1.x.x)
   - `~1.0.0` - Allow patch only (1.0.x)
   - `1.0.0` - Exact version (strict)

---

## 6. Common Workflows

### Initial Setup (New Developer)

```bash
# Clone repo
git clone <repo-url>
cd cloudflare

# Run setup script
./setup.sh

# Or manually:
uv sync                        # Python
cd app/worker && npm install   # Worker
cd app/worker/scripts && ./setup.sh  # CloudFlare
```

### Daily Development

```bash
# Start Python backend
uv run uvicorn app.ensenia.main:app --reload

# In another terminal, start Worker
cd app/worker && npm run dev
```

### Adding Dependencies

**Python**:
```bash
# Production dependency
uv add requests

# Dev dependency
uv add --dev pytest

# Commit changes
git add pyproject.toml uv.lock
git commit -m "Add requests dependency"
```

**Worker**:
```bash
cd app/worker

# Production dependency
npm install axios

# Dev dependency
npm install --save-dev @types/node

# Commit changes
git add package.json package-lock.json
git commit -m "Add axios dependency"
```

### Cleaning & Reinstalling

```bash
# Clean everything
make clean

# Or manually:
rm -rf .venv uv.lock
cd app/worker && rm -rf node_modules package-lock.json

# Reinstall
make install
# Or: uv sync && cd app/worker && npm install
```

---

## 7. Troubleshooting

### Python: "Module not found"

```bash
# Reinstall dependencies
uv sync

# Or clear cache and reinstall
rm -rf .venv uv.lock
uv sync

# Verify environment
uv run python -c "import fastapi; print(fastapi.__version__)"
```

### Worker: "Cannot find module"

```bash
cd app/worker

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Clear npm cache if needed
npm cache clean --force
npm install
```

### Different Versions on Different Machines

**Cause**: Lock files not committed

**Fix**:
```bash
# Ensure lock files are committed
git add uv.lock app/worker/package-lock.json
git commit -m "Add lock files"
```

### uv vs pip Confusion

**Don't mix them!** Stick with `uv`:

```bash
# ❌ Don't use pip
pip install requests

# ✅ Use uv
uv add requests
```

---

## 8. CI/CD Integration

### GitHub Actions Example

```yaml
name: CI

on: [push, pull_request]

jobs:
  test-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install Python dependencies
        run: uv sync

      - name: Run tests
        run: uv run pytest

  test-worker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: cd app/worker && npm install

      - name: Type check
        run: cd app/worker && npm run type-check
```

---

## 9. Best Practices

### DO ✅

- ✅ Commit lock files (`uv.lock`, `package-lock.json`)
- ✅ Use `uv sync` / `npm install` before starting work
- ✅ Run tests after dependency updates
- ✅ Use semantic versioning constraints
- ✅ Keep dependencies up to date
- ✅ Document unusual dependencies

### DON'T ❌

- ❌ Commit `node_modules/` or `.venv/`
- ❌ Mix `pip` and `uv`
- ❌ Edit lock files manually
- ❌ Use `sudo` with package managers
- ❌ Install globally when local works
- ❌ Ignore security updates

---

## 10. Quick Reference

| Task | Python (uv) | Worker (npm) |
|------|-------------|--------------|
| **Install all** | `uv sync` | `npm install` |
| **Add package** | `uv add <pkg>` | `npm install <pkg>` |
| **Add dev package** | `uv add --dev <pkg>` | `npm install --save-dev <pkg>` |
| **Remove package** | `uv remove <pkg>` | `npm uninstall <pkg>` |
| **Update all** | `uv lock --upgrade` | `npm update` |
| **Run command** | `uv run <cmd>` | `npm run <script>` |
| **Clean** | `rm -rf .venv uv.lock` | `rm -rf node_modules package-lock.json` |
| **Lock file** | `uv.lock` (commit) | `package-lock.json` (commit) |
| **Deps folder** | `.venv/` (ignore) | `node_modules/` (ignore) |

---

## 11. Resources

### uv Documentation
- Website: https://github.com/astral-sh/uv
- Docs: https://docs.astral.sh/uv/

### npm Documentation
- Website: https://www.npmjs.com/
- Docs: https://docs.npmjs.com/

### CloudFlare Wrangler
- Docs: https://developers.cloudflare.com/workers/wrangler/

---

**Happy coding! 🚀**
