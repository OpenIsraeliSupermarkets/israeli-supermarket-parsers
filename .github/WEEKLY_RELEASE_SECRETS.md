# Release and CI secrets

## How to release (parsers)

This repo uses [Release Please](https://github.com/googleapis/release-please).
There is no weekly bump script and no rotating `RELEASE_GITHUB_TOKEN`.

1. Merge work to `main` with [Conventional Commits](https://www.conventionalcommits.org/)
   in the PR title (or commits, if you do not squash):
   - `fix:` → patch
   - `feat:` → minor
   - `feat!:` / `BREAKING CHANGE:` → major
   - `chore:` / `docs:` / `ci:` → no release
2. Release Please opens or updates one PR, e.g. `chore(main): release 1.0.7`
   (`setup.py` + `CHANGELOG.md`).
3. **When you want to ship, merge that Release PR.** That is the only release action.
4. The same workflow then tags `vX.Y.Z`, creates the GitHub Release, publishes to
   PyPI, and notifies daily-publish. Those follow-up jobs run in-workflow because
   `GITHUB_TOKEN` cannot start other workflows.

One-time GitHub setting: **Settings → Actions → General → Allow GitHub Actions
to create and approve pull requests** must be enabled, or the Release PR cannot
be opened.

Optional: delete the unused `RELEASE_GITHUB_TOKEN` secret.

## israeli-supermarket-scarpers
| Secret | Required | Purpose |
|--------|----------|---------|
| `CURSOR_MAINTAINER_WEBHOOK` | for maintainer | POST after new CI issue |
| `CURSOR_WEBHOOK_SECRET` | optional | Bearer token for webhook |
| `PARSERS_REPO_TOKEN` | for sync issue | PAT with `issues:write` on parsers |
| `PARSERS_MAINTAINER_WEBHOOK` | for sync | parsers maintainer webhook URL (same as parsers `CURSOR_MAINTAINER_WEBHOOK`) |
| `PARSERS_MAINTAINER_WEBHOOK_SECRET` | optional | Bearer for that webhook |
| `DAILY_PUBLISH_DISPATCH_TOKEN` | for coordinator signal | PAT with `actions:write` (repo dispatch) on daily-publish |

## israeli-supermarket-parsers
| Secret | Required | Purpose |
|--------|----------|---------|
| `CURSOR_MAINTAINER_WEBHOOK` | for maintainer | POST after new CI / sync issue |
| `CURSOR_WEBHOOK_SECRET` | optional | Bearer token |
| `DAILY_PUBLISH_DISPATCH_TOKEN` | for coordinator signal + deps issues | same as scrapers |
| `PYPI` | for publish | PyPI API token used by `python-publish.yml` |

## daily-publish-supermarket-data
| Secret | Required | Purpose |
|--------|----------|---------|
| `WEEKLY_COORDINATOR_TOKEN` | yes | PAT: read Actions on scrapers+parsers; push branch + open PR here |

## Cursor Automations (manual)
1. Scrapers: webhook trigger → maintainer (CI issues).
2. Parsers: webhook trigger → maintainer (CI + `[sync]` issues; may noop).
