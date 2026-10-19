# Contributing

## Pull requests, not direct maintenance pushes

The initial empty scaffold is the only approved direct-to-`main` bootstrap.
All subsequent improvements belong on a feature branch and in a pull request.
Agents and automation must never merge PRs, enable auto-merge, force-push the
default branch, or treat an opened PR as a published release. A maintainer
reviews and explicitly decides whether to merge. This is repository policy;
it does not claim that GitHub branch protection is configured.

Keep one coherent change per PR. Describe the problem, reusable lesson, sources,
tests actually run, and limitations. Use a short conventional commit subject
such as `docs: clarify package scope` or `feat: add a reviewed skill`.

## Authoring a package

1. Confirm that the topic belongs in this repository (see README Scope).
2. Create `skills/<name>/SKILL.md`. Use a stable lowercase ASCII slug with single
   hyphens, at most 64 characters. The frontmatter `name` must match exactly.
3. Start the file at byte zero with YAML frontmatter delimited by lines containing
   `---`. Follow the [Agent Skills specification](https://agentskills.io/specification):
   a nonempty `description` of at most 1024 characters, optional `license`,
   `compatibility`, `allowed-tools`, and a string-to-string `metadata` mapping.
   Prefer concise task-routing descriptions; put author/version/tag strings in
   `metadata`, not new top-level fields. Use block YAML, not flow collections.
4. Write a real instruction body, not a placeholder. Explain applicability,
   decision steps, verification, and known failure cases. Keep detailed material
   in package-local `references/`, `scripts/`, `templates/`, or `assets/`.
5. Use ordinary relative Markdown links for support files. Each package must
   work independently: no links outside its directory, adjacent-package file
   dependencies, symlinks, or nested/alternate `SKILL.md` entrypoints. Do not rely
   on repository-level files being copied during a single-package installation.
6. Cite authoritative sources for technical claims. Record version constraints
   and reviewed source revisions when relevant. Exercise commands in disposable
   fixtures; distinguish source review, structural validation, and runtime tests.
   Never invent verification output or unsupported API behavior.
7. Preserve licenses and attribution. Contribute only material you have the right
   to publish; public visibility alone is not permission to copy. Independently
   research guidance rather than importing personal runtime skills or transcripts.
8. Add the package to the README catalog and replace the conditional installation
   examples with verified discovery/inspection instructions for actual packages.
   Run package-discovery checks when the first package exists. Add grouping
   metadata only if useful, and validate it against its published schema.

Do not publish secrets, credentials, private URLs, local absolute paths, account
inventories, personal memory, or raw session logs. `.gitignore` is a convenience,
not a secret scanner. Review every staged file, including new support files.

## Validation and evidence

Run the README validation commands before opening a PR. The repository validator
calls the official `skills-ref` validator for every package, then supplements it
with strict raw metadata checks and package-local Markdown-link checks. Unit
tests use synthetic temporary fixtures; they are not published skills.

The validator accepts a genuinely empty `skills/` directory (optionally containing
an empty `.gitkeep`). It does not silently ignore malformed or hidden directories.
Missing `SKILL.md`, unexpected top-level files, malformed frontmatter, broken
local links, and escaping links fail the check.

Validation does not execute skill scripts, fetch external links, check anchor
names, inspect inline-code paths or raw HTML links, scan secrets, or prove domain
correctness. Include separate evidence for those concerns when relevant. CI runs
on pull requests with a read-only token, without repository secrets or publishing
steps. Do not replace `pull_request` with privileged execution of untrusted code.

For validator changes, add a regression test that fails before the fix and passes
after it. Keep the two boundary cases covered: no packages yet and a real valid
package, plus representative invalid inputs. Pin tooling updates deliberately
and report any changed validation behavior. Request independent review for
meaningful content or infrastructure changes.
