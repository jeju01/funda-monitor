"""
Publishes docs/index.html to GitHub Pages by committing and pushing.
Uses a Personal Access Token from the .env file — no password needed.
"""

import logging
import os
import subprocess
from datetime import date
from pathlib import Path

from config import BASE_DIR

logger = logging.getLogger(__name__)


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode, (result.stdout + result.stderr).strip()


def publish_dashboard() -> bool:
    today     = date.today().strftime("%Y-%m-%d")
    token     = os.environ.get("GITHUB_TOKEN")
    username  = os.environ.get("GITHUB_USERNAME")
    repo      = os.environ.get("GITHUB_REPO")

    if not all([token, username, repo]):
        logger.error("GITHUB_TOKEN, GITHUB_USERNAME of GITHUB_REPO ontbreekt in .env")
        return False

    remote_url = f"https://{username}:{token}@github.com/{username}/{repo}.git"

    # Git identity
    _run(["git", "config", "user.email", f"{username}@users.noreply.github.com"], BASE_DIR)
    _run(["git", "config", "user.name", "Vastgoedmonitor"], BASE_DIR)

    # Zorg dat remote klopt
    code, _ = _run(["git", "remote", "get-url", "origin"], BASE_DIR)
    if code == 0:
        _run(["git", "remote", "set-url", "origin", remote_url], BASE_DIR)
    else:
        _run(["git", "remote", "add", "origin", remote_url], BASE_DIR)

    # Stage dashboard en snapshot
    for path in ["docs/index.html", "snapshot.json"]:
        _run(["git", "add", path], BASE_DIR)

    code, out = _run(["git", "status", "--porcelain"], BASE_DIR)
    if not out.strip():
        logger.info("Geen wijzigingen — niets te pushen.")
        return True

    code, out = _run(["git", "commit", "-m", f"dashboard: update {today}"], BASE_DIR)
    if code != 0:
        logger.error(f"git commit mislukt: {out}")
        return False

    code, out = _run(["git", "push", "-u", "origin", "main"], BASE_DIR)
    if code != 0:
        logger.error(f"git push mislukt: {out}")
        return False

    logger.info(f"Dashboard live op: https://{username}.github.io/{repo}/")
    return True
