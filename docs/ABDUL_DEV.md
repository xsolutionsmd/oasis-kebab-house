# Abdul's development environment

Preview: https://oasis-abdul-dev.xsolutionsmd.com
Admin: https://oasis-abdul-dev.xsolutionsmd.com/admin
Source: https://github.com/xsolutionsmd/oasis-kebab-house/tree/abdul-dev

## Work and review remotely

```sh
git clone --branch abdul-dev https://github.com/xsolutionsmd/oasis-kebab-house.git
cd oasis-kebab-house
bash start.sh
```

Windows can use `./app.ps1 start`. Git, Python3.10+ and Docker Desktop/Linux containers are required. Local preview is http://127.0.0.1:8789. Run `./app.ps1 check` or `bash app.sh check`, commit and push to `abdul-dev`. The **Abdul dev preview** Action checks, publishes an immutable preview image and waits for Oracle's exact HTTPS revision. Both partners can use the preview URL while discussing changes. GitHub Actions/environment history records what was deployed; `/version.json` reports the exact commit.

To update an existing clean clone, switch to `abdul-dev` and run `./app.ps1 update` or `bash update.sh`. Uncommitted or diverged changes are refused. Local data stays local. Installed mode still follows main; use the source development mode for this branch.

## Promote an agreed change

Open a pull request from `abdul-dev` into `main`, review the diff together and wait for the main branch's required checks. A deliberate merge publishes the main website. Do not auto-merge or delete the long-lived `abdul-dev` branch. After merging, fetch and merge `origin/main` back into `abdul-dev`, then push. This resynchronizes the preview with the approved site. The preview publisher is branch-restricted and remains inactive on main even when its files are merged.

## Isolation and operations

The preview uses Compose project `oasis-abdul-dev`, alias `oasis-abdul-dev-app`, `/opt/oasis-abdul-dev/data`, root-only runtime configuration, separate database/encryption/session keys, separate OAuth client, and image package `ghcr.io/xsolutionsmd/oasis-kebab-house-abdul-dev`. Production data and sender credentials are never copied. Demo mode/noindex remain enabled. Email is initially unconnected; test requests are stored only in the preview.

Google admin sign-in remains separate from sending email. Team membership is also separate from the main site. Both partners can manage this preview; no production team permissions are changed.

The checked release asset is `abdul-dev-<full-sha>/deployment.json`, marked as a prerelease and never latest. The root-owned updater follows only `abdul-dev`, rejects superseded revisions/wrong images, and deploys by digest. Main's publisher, release tags, updater, data and route are unchanged. There is no GitHub-to-server SSH key. Preview publishes automatically on push; use GitHub Actions > the failed run > Re-run failed jobs to retry. Manual workflow dispatch becomes available after the workflow also exists on the repository default branch.

Installer: `sudo bash server/abdul-dev/install.sh`. Runtime secrets must already exist in `/opt/oasis-abdul-dev/runtime.env` (root0600). Route fragment: `deploy/abdul-dev.caddy`. Enable first deployment with `sudo systemctl enable --now oasis-abdul-dev-update.timer` after routing/setup. Never install production's scripts over this preview or vice versa.

Status: `sudo systemctl status oasis-abdul-dev-update.timer`; logs: `sudo journalctl -u oasis-abdul-dev-update.service -n60 --no-pager`; receipt: `/var/lib/oasis-abdul-dev-deploy/current.json`. Daily consistent database/key/config backups run at06:20UTC using `oasis-abdul-dev-backup.timer`; immediate snapshot: `sudo oasis-abdul-dev-backup`. Same-server backups need an off-server copy for host-loss recovery.

Replacement snapshots preserve test data. Handled failure restores matched data/config/image; interrupted or failed recovery leaves a transaction guard for inspection. Do not simply delete it. Preview image retention keeps current plus two proven previous successful sets, with a24-hour grace period, scoped to its package. No global prune or volume deletion.
