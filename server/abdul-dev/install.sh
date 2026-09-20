#!/usr/bin/env bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Run with sudo on the prepared server.' >&2; exit 1; }
cd "$(dirname "$0")/../.."
for command in docker curl git python3 flock timeout sync systemctl; do command -v "$command" >/dev/null; done
docker compose version >/dev/null
docker network inspect xsolutions-proxy >/dev/null
[[ $(uname -m) == aarch64 ]] || { echo 'This installation expects ARM64.' >&2; exit 1; }
for path in /opt/oasis-abdul-dev /var/lib/oasis-abdul-dev-deploy /usr/local/share/oasis-abdul-dev; do
  [[ ! -L "$path" ]] || { echo 'Installation directories must not be symlinks.' >&2; exit 1; }
done
was_active=false
if systemctl is-active --quiet oasis-abdul-dev-update.timer; then was_active=true; fi
if systemctl cat oasis-abdul-dev-update.timer >/dev/null 2>&1; then systemctl stop oasis-abdul-dev-update.timer; fi
if systemctl cat oasis-abdul-dev-update.service >/dev/null 2>&1; then systemctl stop oasis-abdul-dev-update.service; fi
install -d -o root -g root -m 755 /opt/oasis-abdul-dev /usr/local/share/oasis-abdul-dev
install -d -o root -g root -m 700 /var/lib/oasis-abdul-dev-deploy
install -d -o 10001 -g 10001 -m 700 /opt/oasis-abdul-dev/data
test -f /opt/oasis-abdul-dev/runtime.env || { echo 'Prepare /opt/oasis-abdul-dev/runtime.env with mode 600 before installation.' >&2; exit 1; }
chown root:root /opt/oasis-abdul-dev/runtime.env
chmod 600 /opt/oasis-abdul-dev/runtime.env
# Serialize administrator installation with any directly invoked updater too.
exec 9>/var/lib/oasis-abdul-dev-deploy/update.lock
flock -w 120 9
install -o root -g root -m 644 server/abdul-dev/compose.yaml /usr/local/share/oasis-abdul-dev/compose.yaml
install -o root -g root -m 755 server/abdul-dev/update-release.sh /usr/local/sbin/oasis-abdul-dev-update
install -o root -g root -m 755 server/abdul-dev/backup.py /usr/local/sbin/oasis-abdul-dev-backup
install -o root -g root -m 644 server/abdul-dev/oasis-abdul-dev-backup.service /etc/systemd/system/oasis-abdul-dev-backup.service
install -o root -g root -m 644 server/abdul-dev/oasis-abdul-dev-backup.timer /etc/systemd/system/oasis-abdul-dev-backup.timer
install -o root -g root -m 644 server/abdul-dev/oasis-abdul-dev-update.service /etc/systemd/system/oasis-abdul-dev-update.service
install -o root -g root -m 644 server/abdul-dev/oasis-abdul-dev-update.timer /etc/systemd/system/oasis-abdul-dev-update.timer
# The retention observer and timer use this application's updater lock.
# Release our installation lock before installing the observer and shared timer.
flock -u 9
exec 9>&-
python3 server/retention/install_retention.py --config server/abdul-dev/retention.json --service oasis-abdul-dev-update.service
systemctl daemon-reload
systemctl enable --now oasis-abdul-dev-backup.timer
if [[ "$was_active" == true ]]; then systemctl start oasis-abdul-dev-update.timer; fi
echo 'Installed oasis runtime and automatic image retention; existing app timer state preserved. For first setup, prepare HTTPS route then enable --now oasis-abdul-dev-update.timer.'
