#!/usr/bin/env python3
"""Validate an empty scaffold or every independently installable skill package.

This is structural validation, not a security scan or a domain/runtime test.
CommonMark links are checked locally; external URLs are not fetched. Code
examples, inline-code paths, raw HTML links and fragment identifiers are not
link-checked. No package scripts are executed.
"""

import argparse
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
from skills_ref import validate as official_validate
import strictyaml


PACKAGE_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
MARKDOWN = MarkdownIt("commonmark", {"html": False})


def read_text(path: Path, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: cannot read UTF-8 text: {exc}")
        return None


def frontmatter(path: Path, text: str, errors: list[str]) -> tuple[dict, str] | None:
    """Check raw StrictYAML before skills-ref coerces nested metadata to strings."""
    if not text.startswith("---\n"):
        errors.append(f"{path}: frontmatter must start at byte zero with --- on its own line")
        return None
    lines = text.splitlines(keepends=True)
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        errors.append(f"{path}: missing closing frontmatter delimiter")
        return None
    try:
        data = strictyaml.load("".join(lines[1:end])).data
    except strictyaml.YAMLError as exc:
        errors.append(f"{path}: invalid YAML: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{path}: frontmatter must be a mapping")
        return None
    body = "".join(lines[end + 1:])
    if not body.strip():
        errors.append(f"{path}: instruction body must not be empty")
    if data.get("name") != path.parent.name:
        errors.append(f"{path}: name must exactly match the package directory")
    metadata = data.get("metadata")
    if "metadata" in data and (
        not isinstance(metadata, dict)
        or not all(isinstance(k, str) and isinstance(v, str) for k, v in metadata.items())
    ):
        errors.append(f"{path}: metadata must map strings to strings")
    for field in ("license", "compatibility", "allowed-tools"):
        if field in data and (not isinstance(data[field], str) or not data[field].strip()):
            errors.append(f"{path}: {field} must be a nonempty string")
    return data, body


def package_files(package: Path, errors: list[str]) -> list[Path]:
    """Walk without following symlinks, rejecting alternate discovery roots."""
    files = []

    def onerror(exc: OSError) -> None:
        errors.append(f"{package}: cannot inspect package: {exc}")

    for directory, subdirs, filenames in os.walk(package, followlinks=False, onerror=onerror):
        for name in sorted(subdirs + filenames):
            path = Path(directory) / name
            if path.is_symlink():
                errors.append(f"{path}: symlinks are not allowed in skill packages")
                if name in subdirs:
                    subdirs.remove(name)
                continue
            if name in filenames:
                if not path.is_file():
                    errors.append(f"{path}: only regular files are allowed")
                    continue
                files.append(path)
                if name.lower() == "skill.md" and path != package / "SKILL.md":
                    errors.append(f"{path}: nested or alternate skill entrypoint is not allowed")
        subdirs.sort()
    return sorted(files)


def link_targets(tokens):
    for token in tokens:
        if token.type == "link_open":
            yield token.attrGet("href")
        elif token.type == "image":
            yield token.attrGet("src")
        if token.children:
            yield from link_targets(token.children)


def validate_links(path: Path, package: Path, text: str, errors: list[str]) -> None:
    for target in link_targets(MARKDOWN.parse(text)):
        if not isinstance(target, str) or not target or target.startswith(("#", "//")):
            continue
        try:
            url = urlsplit(target)
            if url.scheme and url.scheme.lower() != "file":
                continue
            if url.scheme.lower() == "file":
                errors.append(f"{path}: local link escapes package: {target}")
                continue
            local = unquote(url.path)
            if not local:
                continue
            candidate = (path.parent / local).resolve()
            if Path(local).is_absolute() or not candidate.is_relative_to(package.resolve()):
                errors.append(f"{path}: local link escapes package: {target}")
            elif not candidate.exists():
                errors.append(f"{path}: missing local link: {target}")
        except (OSError, ValueError, RuntimeError) as exc:
            errors.append(f"{path}: invalid local link {target!r}: {exc}")


def validate_package(package: Path, errors: list[str]) -> None:
    before = len(errors)
    files = package_files(package, errors)
    path = package / "SKILL.md"
    if path not in files:
        errors.append(f"{package}: missing SKILL.md")
        return
    if len(errors) != before:
        return
    text = read_text(path, errors)
    if text is None:
        return
    parsed = frontmatter(path, text, errors)
    if parsed is None:
        return
    try:
        errors.extend(f"{path}: Agent Skills: {error}" for error in official_validate(package))
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        errors.append(f"{path}: Agent Skills validation could not complete: {exc}")
    for markdown_path in files:
        if markdown_path.suffix.lower() != ".md":
            continue
        markdown = parsed[1] if markdown_path == path else read_text(markdown_path, errors)
        if markdown is not None:
            validate_links(markdown_path, package, markdown, errors)


def validate_repository(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    names: list[str] = []
    skills = Path(root) / "skills"
    if skills.is_symlink():
        return names, [f"{skills}: symlinks are not allowed"]
    if not skills.is_dir():
        return names, [f"{skills}: missing skills directory"]
    try:
        entries = sorted(skills.iterdir())
    except OSError as exc:
        return names, [f"{skills}: cannot list directory: {exc}"]
    for entry in entries:
        if entry.is_symlink():
            errors.append(f"{entry}: symlinks are not allowed")
        elif entry.name == ".gitkeep" and entry.is_file():
            if entry.stat().st_size:
                errors.append(f"{entry}: .gitkeep must be empty")
        elif not entry.is_dir():
            errors.append(f"{entry}: unexpected entry; use skills/<name>/SKILL.md")
        elif len(entry.name) > 64 or not PACKAGE_NAME.fullmatch(entry.name):
            errors.append(f"{entry}: invalid package directory name (use lowercase ASCII slugs, max 64 characters)")
        else:
            names.append(entry.name)
            validate_package(entry, errors)
    return names, errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    names, errors = validate_repository(args.root)
    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    suffix = " (empty scaffold)" if not names else ": " + ", ".join(names)
    print(f"OK: {len(names)} skill packages{suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
