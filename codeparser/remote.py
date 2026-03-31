from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


GITHUB_HOSTS = {"github.com", "www.github.com"}
GITHUB_API_ACCEPT = "application/vnd.github+json"
USER_AGENT = "CodeParser/1.0"


class RemoteResolutionError(RuntimeError):
    """Raised when a remote repository cannot be resolved locally."""


@dataclass(slots=True)
class GitHubRepoSpec:
    owner: str
    repo: str
    ref: str | None = None
    subdirectory: str = ""
    raw_ref_path: str = ""
    original_url: str = ""

    @property
    def display_name(self) -> str:
        if self.subdirectory:
            return f"{self.repo}-{Path(self.subdirectory).name}"
        return self.repo


@dataclass
class ResolvedTarget:
    root_path: Path
    display_name: str
    source_url: str | None = None
    _temporary_directory: TemporaryDirectory[str] | None = None

    def cleanup(self) -> None:
        if self._temporary_directory is not None:
            self._temporary_directory.cleanup()
            self._temporary_directory = None


def is_github_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and parsed.netloc.lower() in GITHUB_HOSTS


def parse_github_url(value: str) -> GitHubRepoSpec:
    parsed = urlparse(value)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise RemoteResolutionError(
            "GitHub URLs must include both an owner and repository name.",
        )

    owner = parts[0]
    repo = parts[1].removesuffix(".git")

    ref = None
    subdirectory = ""
    raw_ref_path = ""

    if len(parts) > 2 and parts[2] == "tree":
        raw_ref_path = "/".join(parts[3:])
        if parts[3:]:
            ref = parts[3]
            subdirectory = "/".join(parts[4:])

    return GitHubRepoSpec(
        owner=owner,
        repo=repo,
        ref=ref,
        subdirectory=subdirectory,
        raw_ref_path=raw_ref_path,
        original_url=value,
    )


def _github_request(url: str) -> Request:
    return Request(
        url,
        headers={
            "Accept": GITHUB_API_ACCEPT,
            "User-Agent": USER_AGENT,
        },
    )


def _read_json(url: str) -> dict:
    with urlopen(_github_request(url)) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _download_bytes(url: str) -> bytes:
    with urlopen(_github_request(url)) as response:
        return response.read()


def _ref_exists(owner: str, repo: str, ref: str) -> bool:
    encoded_ref = quote(ref, safe="")
    branch_url = f"https://api.github.com/repos/{owner}/{repo}/branches/{encoded_ref}"
    tag_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/tags/{encoded_ref}"

    for url in (branch_url, tag_url):
        try:
            _read_json(url)
            return True
        except HTTPError as exc:
            if exc.code == 404:
                continue
            raise RemoteResolutionError(
                f"GitHub returned HTTP {exc.code} while checking reference '{ref}'.",
            ) from exc
        except URLError as exc:
            raise RemoteResolutionError(
                f"Unable to contact GitHub while checking reference '{ref}': {exc}",
            ) from exc

    return False


def _resolve_ref_and_subdirectory(spec: GitHubRepoSpec) -> tuple[str | None, str]:
    if not spec.raw_ref_path:
        return spec.ref, spec.subdirectory

    segments = [segment for segment in spec.raw_ref_path.split("/") if segment]
    if not segments:
        return spec.ref, spec.subdirectory

    for index in range(len(segments), 0, -1):
        candidate_ref = "/".join(segments[:index])
        candidate_subdir = "/".join(segments[index:])
        if _ref_exists(spec.owner, spec.repo, candidate_ref):
            return candidate_ref, candidate_subdir

    return spec.ref, spec.subdirectory


def _get_default_branch(spec: GitHubRepoSpec) -> str:
    repo_url = f"https://api.github.com/repos/{spec.owner}/{spec.repo}"
    try:
        metadata = _read_json(repo_url)
    except HTTPError as exc:
        raise RemoteResolutionError(
            f"GitHub returned HTTP {exc.code} while fetching repository metadata.",
        ) from exc
    except URLError as exc:
        raise RemoteResolutionError(
            f"Unable to contact GitHub for repository metadata: {exc}",
        ) from exc

    default_branch = metadata.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch.strip():
        raise RemoteResolutionError("GitHub did not return a default branch name.")
    return default_branch


def _extract_archive(archive_bytes: bytes, destination: Path) -> Path:
    archive_path = destination / "repo.zip"
    archive_path.write_bytes(archive_bytes)

    extract_dir = destination / "extract"
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(extract_dir)

    extracted_roots = sorted(path for path in extract_dir.iterdir() if path.is_dir())
    if not extracted_roots:
        raise RemoteResolutionError(
            "The downloaded GitHub archive did not contain a repository root.",
        )
    return extracted_roots[0]


def resolve_github_target(value: str) -> ResolvedTarget:
    spec = parse_github_url(value)
    ref, subdirectory = _resolve_ref_and_subdirectory(spec)
    if not ref:
        ref = _get_default_branch(spec)

    archive_url = (
        f"https://api.github.com/repos/{spec.owner}/{spec.repo}/zipball/{quote(ref, safe='')}"
    )

    temporary_directory = TemporaryDirectory(prefix="codeparser-")
    temp_root = Path(temporary_directory.name)

    try:
        archive_bytes = _download_bytes(archive_url)
        repo_root = _extract_archive(archive_bytes, temp_root)
        resolved_root = repo_root / subdirectory if subdirectory else repo_root
        if not resolved_root.exists() or not resolved_root.is_dir():
            raise RemoteResolutionError(
                f"The GitHub URL points to '{subdirectory}', but that folder was not found.",
            )

        display_name = spec.repo if not subdirectory else f"{spec.repo}-{Path(subdirectory).name}"
        return ResolvedTarget(
            root_path=resolved_root,
            display_name=display_name,
            source_url=value,
            _temporary_directory=temporary_directory,
        )
    except Exception:
        temporary_directory.cleanup()
        raise


def resolve_target(target: str | Path | None) -> ResolvedTarget:
    if isinstance(target, Path):
        root_path = target.expanduser().resolve()
        if not root_path.exists() or not root_path.is_dir():
            raise RemoteResolutionError(f"Folder not found: {root_path}")
        return ResolvedTarget(root_path=root_path, display_name=root_path.name or "repo")

    target_text = (target or "").strip()
    if is_github_url(target_text):
        return resolve_github_target(target_text)

    root_path = Path(target_text or ".").expanduser().resolve()
    if not root_path.exists() or not root_path.is_dir():
        raise RemoteResolutionError(f"Folder not found: {root_path}")
    return ResolvedTarget(root_path=root_path, display_name=root_path.name or "repo")
