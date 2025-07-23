import os
import re
from pathlib import Path
from shutil import copy, move, rmtree
from sys import argv

from github import Github

from . import logger
from .action_timestamp import TimestampFile
from .constants import CACHE_ROOT, DIST_ROOT, TEMPDIR
from .subprocess import execute_mute, execute_output, execute_passthru

refresh_expires = 60 * 60 * 1
is_force = "--force" in argv


def git_clone_or_pull(repo_url: str, branch="", alter_name: str | Path | None = None):
    if alter_name is None:
        p = Path(repo_url)
        base = p.stem if p.suffix == ".git" else p.name
        dir = p.parent.name
        alter_name = f"{dir}/{base}"

    save_path = DIST_ROOT / alter_name
    ts = TimestampFile(save_path / ".git/last_pull_time", refresh_expires)
    if not ts.is_expired():
        logger.dim(
            "    git repo pulled within 1 hour, skipping. set --force to force pull"
        )
        return save_path

    if os.path.exists(save_path):
        remote = execute_output("git", "remote", "get-url", "origin", cwd=save_path)
        if remote != repo_url:
            rmtree(save_path)

    if os.path.exists(save_path):
        # If the directory exists, pull the latest changes
        execute_mute("git", "reset", "--hard", cwd=save_path)
        execute_mute("git", "clean", "-ffdx", cwd=save_path)
        if branch:
            execute_mute("git", "checkout", branch, cwd=save_path)

        execute_passthru("git", "pull", cwd=save_path)
    else:
        # If the directory does not exist, clone the repository
        branch = ["--branch", branch] if branch else []

        execute_passthru(
            "git",
            "clone",
            "--depth",
            "5",
            "--single-branch",
            *branch,
            "--recurse-submodules",
            "--shallow-submodules",
            repo_url,
            save_path.as_posix(),
        )

    ts.update()

    return save_path


gh_token: str | None = os.environ.get("GITHUB_TOKEN", None)
if not gh_token:
    logger.warning("GITHUB_TOKEN is required, place it in .env file")
github_api_instance = None


def github_api() -> Github:
    global github_api_instance
    if not github_api_instance:
        from github import Auth, Github

        auth = Auth.Token(gh_token)
        github_api_instance = Github(auth=auth)

    return github_api_instance


def github_get_release(repo_name: str, pattern: re.Pattern):
    g = github_api()

    repo = g.get_repo(repo_name)
    releases = repo.get_releases().get_page(0)
    latest_release = releases[0]
    assets = latest_release.get_assets()
    for asset in assets:
        if re.search(pattern, asset.name):
            return asset
    return None


def github_download_release(repo_name: str, pattern: re.Pattern):
    file = github_get_release(repo_name, pattern)
    if not file:
        logger.die(f"Cannot find release file for {repo_name} with pattern {pattern}")
    logger.dim(f"    release file: {file.url}")

    distf = CACHE_ROOT / file.name
    if distf.exists() and not is_force:
        logger.dim(f"     - exists: {distf}")
        return distf

    logger.dim(f"     - downloading: {distf}")
    TEMPDIR.mkdir(parents=True, exist_ok=True)
    tempf = TEMPDIR / file.name
    file.download_asset(tempf.as_posix())

    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    copy(tempf, distf)

    return distf
