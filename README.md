# Factorio Modding Skills

A home for reviewed, version-aware agent skills about Factorio mod development.

**Status: scaffold only. There are no published skill packages to install yet.**
`skills/.gitkeep` preserves the intended layout; it is not a skill. Test fixtures
exist only to exercise validation and are not installable content.

## Scope

Future packages may cover Factorio mod-development workflows, testing, and
release hygiene. Technical guidance must be grounded in authoritative sources
for explicit game/API versions and verified against disposable fixtures where
possible. This scaffold makes no Factorio API or runtime-compatibility claims.
It ships no mods, game assets, invented technical skills, or personal runtime
skill copies.

Domain-independent procedures belong in
[agent-skills](https://github.com/SirEdvin/agent-skills). Minecraft-specific
material belongs in
[minecraft-modding-skills](https://github.com/SirEdvin/minecraft-modding-skills).

## Skills

No skill packages are published yet. The first package must arrive through a
reviewed pull request and add a real entry to this catalog.

## Layout

```text
skills/                  # Future independent skills/<name>/SKILL.md packages
scripts/                 # Repository validator and synthetic regression tests
.github/workflows/       # Read-only validation CI
CONTRIBUTING.md           # Authoring, provenance, validation, and PR policy
LICENSE                  # MIT
```

No grouping manifest or release is advertised before packages exist.

## Installation (after skills are published)

**The commands below are future usage templates, not currently working package
installations.** Wait for an actual catalog entry, inspect its content and
license, then set `SKILL_NAME` to its exact directory name. Choose the intended
agent/profile and installation scope; an installation modifies that target.
The POSIX shell guards below prevent an unset package name from being used.

With [Hermes](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills):

```sh
hermes skills inspect "SirEdvin/factorio-modding-skills/skills/${SKILL_NAME:?Set SKILL_NAME to a published package}"
hermes skills install "SirEdvin/factorio-modding-skills/skills/${SKILL_NAME:?Set SKILL_NAME to a published package}"
```

Optional Hermes tap registration and discovery, once the catalog is populated
(registration changes local tap configuration):

```sh
hermes skills tap add SirEdvin/factorio-modding-skills
hermes skills search "${SKILL_NAME:?Set SKILL_NAME to a published package}"
```

With the [skills CLI](https://github.com/vercel-labs/skills), list before installing
and select an agent/scope interactively rather than installing to every agent:

```sh
npx skills add SirEdvin/factorio-modding-skills --list --full-depth
npx skills add SirEdvin/factorio-modding-skills --skill "${SKILL_NAME:?Set SKILL_NAME to a published package}"
```

Review the CLI version before executing downloaded tooling. Multi-file packages
must be installed from a repository package path, not a raw `SKILL.md` URL.
End-to-end discovery and installation are intentionally deferred until real
packages exist; this scaffold does not claim those checks have passed.

## Validate

Use Python 3.12 or newer. From the repository root, create an isolated environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s scripts -p 'test_*.py' -v
.venv/bin/python scripts/validate_skills.py
git diff --check
```

On Windows use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.
If your shell injects `PYTHONPATH` or `PYTHONHOME`, unset them for these commands
so the environment cannot accidentally reuse unrelated installed dependencies.

An empty scaffold prints `OK: 0 skill packages (empty scaffold)` and succeeds.
When packages are added, the same command automatically validates every direct
package directory using pinned [skills-ref](https://pypi.org/project/skills-ref/)
and additional package-boundary checks. It rejects incomplete packages instead
of treating them as an empty repository. CI tests Python 3.12 and 3.14.

Checks cover frontmatter, naming, raw string metadata, symlinks, alternate
entrypoints, and package-local CommonMark links in Markdown files. They do not
execute skill scripts, test domain APIs, fetch external URLs, inspect raw HTML
or inline-code paths, validate anchor names, or perform a security audit.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the exact authoring and review contract.

## Contributions and PR policy

The initial scaffold commit is the sole direct-to-default-branch bootstrap
exception. **All future improvements go through a feature branch and pull
request. Agents and automation must never merge PRs or enable auto-merge.**
A maintainer reviews evidence and explicitly decides whether to merge. This
policy is documented here; it is not a claim of configured branch protection.

Do not copy personal skills or publish private paths, secrets, account data,
or transcripts. Keep contributions portable, attributable, source-grounded,
and independently installable. Read [CONTRIBUTING.md](CONTRIBUTING.md) before
making changes.

## License and conventions

[MIT](LICENSE), matching the existing
[Minecraft skill library](https://github.com/SirEdvin/minecraft-modding-skills).
The `skills/<name>/SKILL.md` layout, portable metadata, package independence,
and PR-evidence conventions follow that public library. This repository starts
with newly authored scaffolding, not imported skill content. Dependencies retain
their own licenses; future third-party material needs explicit provenance and
compatible licensing.
