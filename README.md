# dup‑rename

**What it does**
- Walks a target folder recursively.
- Computes a SHA‑256 hash for each file.
- Groups files that share the same hash (i.e. duplicates).
- Optionally renames duplicates to `original_name_dupN.ext`.
- Sends a concise success/failure message to a Telegram bot (if `TELEGRAM_TOKEN` & `TELEGRAM_CHAT_ID` are set).

**Why this project?**
- Matches TopherBot’s love for *auto‑rename* and *proactive duplicate detection*.
- Demonstrates a complete CI/CD pipeline (lint → test → build → notification) in under 50 lines of code.

**Installation**
```bash
# Clone & install dependencies (only stdlib is required, but we ship a tiny requirements file for CI)
git clone https://github.com/your‑handle/dup‑rename.git
cd dup‑rename
python -m pip install -r requirements.txt   # no external packages, just a placeholder
```

**Usage**
```bash
python dup_rename.py /path/to/scan          # dry‑run, prints duplicates
python dup_rename.py /path/to/scan --rename # rename duplicates in‑place
```

**Telegram notifications**
Set the following secrets in your repo (or export locally) before running:
```bash
export TELEGRAM_TOKEN=123456:ABCDEF...
export TELEGRAM_CHAT_ID=987654321
```
If the env vars are missing, the tool still works – it just skips the notification step.

**CI/CD**
The repository ships a GitHub Actions workflow (`.github/workflows/ci.yml`) that:
1. Checks out code.
2. Runs **Super‑Linter** (parallelised, zero‑config).
3. Installs the tiny `requirements.txt`.
4. Executes `pytest` with a coverage threshold of 80 %.
5. On success, posts a short Telegram message via a curl call (uses the same env vars as the CLI).

**Testing**
We provide a single `test_dup_rename.py` using `pytest`. It creates temporary files, verifies hashing, duplicate grouping, and the rename logic.

**License**
MIT – see the LICENSE file.
