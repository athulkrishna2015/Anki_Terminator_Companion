# AGENTS.md — Anki Terminator Companion

Working notes for coding agents and humans changing this repository.

## What this repo is

A **companion add-on** for `Anki Terminator V2 - ChatGPT DeepSeek Sidebar for Reviewer`
(AnkiWeb addon id `1468920185`, the "target add-on"). It never modifies the target
add-on's directory; it monkey-patches it at import time from the `patch_1468920185_anki_terminator/`
package.

## Repository layout

| Path | Purpose |
|---|---|
| `addon/` | **The shipped add-on.** This directory *is* what ends up in the `.ankiaddon` — `__init__.py` sits at the archive root. |
| `addon/VERSION` | Canonical version. Synced into `addon/manifest.json` by `bump.py` / `make_ankiaddon.py`. |
| `patch_1468920185_anki_terminator/` (inside `addon/`) | The patches. Kept under `addon/` because they are part of the shipped package. |
| `make_ankiaddon.py` | Builds `Anki_Terminator_Companion_v<version>_<timestamp>.ankiaddon`. Honours `.gitignore`. |
| `bump.py` | Version bump + `manifest.json` sync. `python3 bump.py [major\|minor\|patch]`. |
| `docs/` | ARCHITECTURE.md, CONFIGURATION.md, DEVELOPMENT.md |
| `addon/companion.log` | Runtime log. Gitignored, rewritten each Anki launch. **First stop when debugging.** |

The installed copy at `~/.local/share/Anki2/addons21/Anki_Terminator_Companion` is a
**symlink** to `addon/`, so edits take effect on the next Anki restart without reinstalling.

`make_ankiaddon.py` imports `bump.py` from the repo root, so **always run it from the repo root**.

## Releasing (this is the only way an add-on gets onto AnkiWeb)

The pipeline is `.github/workflows/release.yml`. It fires on **exactly one** thing:

```yaml
on:
  release:
    types: [published]      # a release transitioning draft -> published
  workflow_dispatch: ...    # manual rebuild / dry run
```

**The trigger is publishing a release, not the tag.** Creating a draft runs nothing —
that is by design, it is the pause state.

| Action | Uploads to AnkiWeb? |
|---|---|
| `python3 make_ankiaddon.py` locally | No — local file, gitignored |
| `git push origin master` | No |
| `git push origin vX.Y.Z` | No |
| `gh release create vX.Y.Z --draft` | No — drafts run nothing |
| `gh release edit vX.Y.Z --draft=false` | **Yes** |
| `gh release create vX.Y.Z --draft=false` | **Yes** |

### Steps

```bash
# 1. bump (minor for a feature/fix release, patch otherwise)
python3 bump.py minor                    # -> updates addon/VERSION + addon/manifest.json
#   NB: minor bumps drop the patch and give "1.9", not "1.9.0". If you want the
#   full three-part form, run `python3 make_ankiaddon.py 1.9.0` once, which
#   re-syncs both files via sync_version().

# 2. changelog + README
#   - CHANGELOG.md: new "### <Month D, YYYY> (vX.Y.Z)" section at the top.
#   - README.md IS the AnkiWeb listing description (see the workflow's
#     description-file input). Document new user-facing settings there.

# 3. commit + tag + push
git add -A && git commit -m "Bump version to X.Y.Z"
git push origin master
git tag vX.Y.Z && git push origin vX.Y.Z

# 4. create the release PUBLISHED (not draft) -> this fires the workflow
gh release create vX.Y.Z \
  --repo athulkrishna2015/Anki_Terminator_Companion \
  --title "Anki Terminator Companion vX.Y.Z" \
  --notes "..."

# 5. watch it
gh run watch --repo athulkrishna2015/Anki_Terminator_Companion
```

### What the workflow does

1. **Resolve and validate ref** — fails early and legibly if the tag/branch does not
   exist, or (outside `dry_run`) if there is no GitHub release for it.
2. **Derive version** — strips the leading `v` from the tag. A `dry_run` off a branch
   falls back to `addon/VERSION`.
3. **Syntax-check the addon package** — byte-compiles every `*.py` under `addon/`.
   The runner has no Anki and the add-on imports `aqt` at module scope, so importing
   is impossible; byte-compiling is the strongest check available.
4. **Build** — `python3 make_ankiaddon.py <version>`.
5. **Check AnkiWeb description size** — AnkiWeb rejects descriptions over 65535 bytes
   *silently from the add-on's point of view*: the upload fails and the listing keeps
   its old text, so it looks like the README was dropped. Hence the explicit check.
6. **Attach to the GitHub release** (`--clobber`, so re-runs are safe).
7. **Upload to AnkiWeb** via `athulkrishna2015/ankiweb-api@v1`.

### Manual rebuild without cutting a version

Actions → **Release** → **Run workflow** → enter the tag (e.g. `v1.9.0`).
Tick `dry_run` to rehearse the check, build and description-size check without
touching the GitHub release or AnkiWeb.

## AnkiWeb listing — do not get this wrong

| Field | Value |
|---|---|
| addon id | `542586361` |
| title | `Anki_Terminator_Companion` |
| support page | `https://github.com/athulkrishna2015/Anki_Terminator_Companion` |
| branch | `2.1.1-26.05+` |
| description | `README.md` |

**`addon-id` must stay set in the workflow.** The action creates a *brand new* listing
when it is empty — that would orphan the existing one along with its URL, download
count and reviews. The action **replaces** title, tags, support page, branches and
description on every upload, so a wrong value in the workflow silently rewrites the
public listing. Change them deliberately, not as a side effect of an edit.

Branch notation is `MIN-MAX`, where each side is a `2.1.x` patch or `major[.minor[.patch]]`,
with a trailing `+` on max meaning open-ended — e.g. `2.1.1-26.05+`. `2.1.1+` alone is
**not** valid and `upload.py` will reject it.

Verify the live listing against the account:

```bash
cd /mnt/0946E88701BE265B/portable/anki/ankiweb-api
python3 ankicli.py info 542586361                       # title, support, description
python3 ankicli.py call --env-file .env \
  --request '{"addon_id":542586361}' /svc/shared/get-addon-info   # exact tags + branches
```

## Credentials

Two Actions secrets, set once via `gh`:

```bash
set -a; . /mnt/0946E88701BE265B/portable/anki/ankiweb-api/.env; set +a
gh secret set ANKIWEB_USERNAME --repo athulkrishna2015/Anki_Terminator_Companion --body "$ANKIWEB_USERNAME"
gh secret set ANKIWEB_PASSWORD --repo athulkrishna2015/Anki_Terminator_Companion --body "$ANKIWEB_PASSWORD"
```

- **Never commit `.env`** or paste the values into a file, a log or an issue.
- Plain-password auth only; interactive 2FA is unsupported by the client.
- `ankiweb-api/.env` also holds `ANKIWEB_TEST_ADDON_ID`, a **private throwaway add-on**
  (805854302) used for client upload tests. Do not point the release workflow at it.

## Coding conventions

- Target the **currently installed Anki** (`anki --version`). The host runs a rolling
  release build, and `aqt.gui_hooks` **changed shape in 26.x**: hooks are custom
  `_aqt.hooks.*` objects exposing only `append`/`remove`/`count`, not plain lists.
  `x in hook`, `len(hook)` and `for x in hook` all raise `TypeError`. To test membership,
  read `hook._hooks` (the backing list) and fall back to the object itself for older Anki.
- Always guard optional hooks with `hasattr`/`getattr` — hook names come and go between
  versions.
- The add-on **swallows exceptions broadly** and reports them via `companion.log`. If the
  log shows `...patch failed: ...`, that patch is dead even though startup "succeeded".
  Always check the log after a change.
- Deep-freeze timer state lives on the sidebar widget as `_deep_freeze_timer` /
  `_deep_frozen_url`; clean up with the provided helpers rather than reaching for
  `QTimer` directly.