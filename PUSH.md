# How to push this project to GitHub

If you cloned this via a bundle or tarball, here's how to push to your GitHub repo.

## Option 1 — From a git bundle (preserves history)

```bash
git clone /path/to/nexus-ai.bundle nexus-ai
cd nexus-ai
git remote set-url origin https://github.com/Varich22/nexus-ai.git
git push -u origin main
```

## Option 2 — From a tarball (fresh history)

```bash
mkdir nexus-ai && tar -xzf nexus-ai.tar.gz -C nexus-ai --strip-components=1
cd nexus-ai
git init
git add .
git commit -m "feat: initial backend MVP"
git remote add origin https://github.com/Varich22/nexus-ai.git
git push -u origin main
```

## After pushing

1. On GitHub, go to **Settings → Secrets and variables → Actions**
2. Add a secret `OPENAI_API_KEY_TEST` (optional, for CI tests)
3. Clone your repo locally: `git clone https://github.com/Varich22/nexus-ai.git`
4. `cd nexus-ai && cp .env.example .env`
5. Edit `.env` and paste your real `OPENAI_API_KEY`
6. Run: `docker compose up` or `cd backend && pip install -e ".[dev]" && uvicorn app.main:app --reload`
