# Pre-Commit Checklist

Before committing to GitHub, make sure:

## ✅ Files to Commit

- [x] All source code (`.py` files)
- [x] Templates (`.html` files)
- [x] Configuration files (`requirements.txt`, `Dockerfile`, `docker-compose.yml`)
- [x] Documentation (`.md` files)
- [x] GitHub Actions workflows (`.github/workflows/*.yml`)
- [x] Alembic migrations (`alembic/versions/*.py`)
- [x] `.env.example` (template, no secrets)
- [x] `.gitignore` (properly configured)

## ❌ Files NOT to Commit

- [ ] `.env` (contains secrets - should be in .gitignore)
- [ ] `__pycache__/` (Python cache)
- [ ] `venv/` or `.venv/` (virtual environment)
- [ ] `*.log` (log files)
- [ ] `*.db` or `*.sqlite` (local databases)
- [ ] `.DS_Store` (macOS files)
- [ ] IDE files (`.vscode/`, `.idea/`)

## 🔒 Secrets Check

**NEVER commit:**
- Database passwords
- API keys
- Email credentials
- Any `.env` file

**Safe to commit:**
- `.env.example` (template with placeholder values)

## 📝 Before First Commit

1. **Verify .gitignore is correct:**
   ```bash
   cat .gitignore
   ```

2. **Check what will be committed:**
   ```bash
   git status
   ```

3. **Verify no secrets are included:**
   ```bash
   git diff
   # Check for any API keys, passwords, etc.
   ```

4. **Make sure .env is ignored:**
   ```bash
   git check-ignore .env
   # Should output: .env
   ```

## 🚀 Ready to Commit

```bash
# Add files
git add .

# Check what's staged
git status

# Commit
git commit -m "Initial commit: Raider Power Zone Forecasting app"

# Push to GitHub
git push origin main
```

## ⚠️ If You Accidentally Committed Secrets

If you accidentally committed secrets:

1. **Remove from history:**
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   ```

2. **Or use BFG Repo-Cleaner** (easier):
   ```bash
   bfg --delete-files .env
   ```

3. **Force push** (⚠️ only if you're sure):
   ```bash
   git push origin --force --all
   ```

4. **Rotate all secrets** (change API keys, passwords, etc.)
