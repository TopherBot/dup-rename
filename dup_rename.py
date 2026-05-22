#!/usr/bin/env python3
"""dup‑rename – detect and optionally rename duplicate files.

Features:
- Recursive scan, SHA‑256 hash based duplicate detection.
- Auto‑rename duplicates to ``<basename>_dupN<ext>``.
- Graceful error handling (permissions, read errors).
- Optional Telegram notification via Bot API.
"""

import argparse
import hashlib
import os
import sys
import json
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

# ------------------------------------------------------------
# Helper utilities
# ------------------------------------------------------------

def sha256_file(path: Path) -> str:
    """Return the SHA‑256 hex digest of *path*.
    Errors are caught and reported as an empty string so the caller can decide.
    """
    try:
        hasher = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"[WARN] Could not hash {path}: {e}", file=sys.stderr)
        return ""

def group_by_hash(root: Path) -> Dict[str, List[Path]]:
    """Walk *root* and return a mapping hash → list of files sharing that hash."""
    hash_map: Dict[str, List[Path]] = defaultdict(list)
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            file_path = Path(dirpath) / name
            h = sha256_file(file_path)
            if h:
                hash_map[h].append(file_path)
    return {h: lst for h, lst in hash_map.items() if len(lst) > 1}

def auto_rename(duplicates: Dict[str, List[Path]]) -> List[Tuple[Path, Path]]:
    """Rename all but the first file in each duplicate group.
    Returns a list of (old_path, new_path) tuples.
    """
    renamed = []
    for paths in duplicates.values():
        # Keep the first file untouched; rename the rest
        for idx, old_path in enumerate(paths[1:], start=1):
            stem = old_path.stem
            suffix = old_path.suffix
            new_name = f"{stem}_dup{idx}{suffix}"
            new_path = old_path.with_name(new_name)
            try:
                old_path.rename(new_path)
                renamed.append((old_path, new_path))
            except Exception as e:
                print(f"[ERROR] Failed to rename {old_path} → {new_path}: {e}", file=sys.stderr)
    return renamed

def send_telegram(message: str) -> None:
    """Send *message* via Telegram Bot API if env vars are present."""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[INFO] Telegram credentials not set – skipping notification.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": message}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Telegram API error: {resp.status}")
    except Exception as e:
        print(f"[WARN] Telegram notification failed: {e}", file=sys.stderr)

# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Detect and optionally rename duplicate files.")
    parser.add_argument("path", type=Path, help="Root directory to scan")
    parser.add_argument("--rename", action="store_true", help="Rename duplicates in‑place")
    args = parser.parse_args()

    if not args.path.is_dir():
        print(f"[ERROR] {args.path} is not a directory", file=sys.stderr)
        sys.exit(1)

    duplicates = group_by_hash(args.path)
    if not duplicates:
        print("No duplicates found.")
        send_telegram("✅ dup‑rename: No duplicates detected.")
        return

    # Print report
    print("Duplicates found:")
    for h, files in duplicates.items():
        print(f"  Hash {h[:8]}…:")
        for p in files:
            print(f"    - {p}")

    renamed = []
    if args.rename:
        renamed = auto_rename(duplicates)
        print("\nRenamed files:")
        for old, new in renamed:
            print(f"  {old} → {new}")

    # Build a short Telegram summary
    msg = f"🔎 dup‑rename report for `{args.path}`\n"
    msg += f"*Duplicates:* {sum(len(v) for v in duplicates.values())}\n"
    if args.rename:
        msg += f"*Renamed:* {len(renamed)}"
    else:
        msg += "*Renamed:* 0 (dry‑run)"
    send_telegram(msg)

if __name__ == "__main__":
    main()
