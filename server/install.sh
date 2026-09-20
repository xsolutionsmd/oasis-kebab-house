#!/usr/bin/env bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Run with sudo on the prepared server.' >&2; exit 1; }
cd "$(dirname "$0")/.."
for command in docker curl git python3 flock timeout sync systemctl; do command -v "$command" >/dev/null; done
docker compose version >/dev/null
docker network inspect xsolutions-proxy >/dev/null
[[ $(uname -m) == aarch64 ]] || { echo 'This installation expects ARM64.' >&2; exit 1; }
for path in /opt/oasis /var/lib/oasis-deploy /usr/local/share/oasis; do
  [[ ! -L "$path" ]] || { echo 'Installation directories must not be symlinks.' >&2; exit 1; }
done
was_active=false
if systemctl is-active --quiet oasis-update.timer; then was_active=true; fi
if systemctl cat oasis-update.timer >/dev/null 2>&1; then systemctl stop oasis-update.timer; fi
if systemctl cat oasis-update.service >/dev/null 2>&1; then systemctl stop oasis-update.service; fi
install -d -o root -g root -m 755 /opt/oasis /usr/local/share/oasis
install -d -o root -g root -m 700 /var/lib/oasis-deploy
install -d -o 10001 -g 10001 -m 700 /opt/oasis/data
test -f /opt/oasis/runtime.env || { echo 'Prepare /opt/oasis/runtime.env with mode 600 before installation.' >&2; exit 1; }
chown root:root /opt/oasis/runtime.env
chmod 600 /opt/oasis/runtime.env
# Serialize administrator installation with any directly invoked updater too.
exec 9>/var/lib/oasis-deploy/update.lock
flock -w 120 9
install -o root -g root -m 644 compose.production.yaml /usr/local/share/oasis/compose.yaml
install -o root -g root -m 755 server/update-release.sh /usr/local/sbin/oasis-update
install -o root -g root -m 755 server/backup.py /usr/local/sbin/oasis-backup
install -o root -g root -m 644 server/oasis-backup.service /etc/systemd/system/oasis-backup.service
install -o root -g root -m 644 server/oasis-backup.timer /etc/systemd/system/oasis-backup.timer
install -o root -g root -m 644 server/oasis-update.service /etc/systemd/system/oasis-update.service
install -o root -g root -m 644 server/oasis-update.timer /etc/systemd/system/oasis-update.timer
# The retention observer and timer use this application's updater lock.
# Release our installation lock before installing the observer and shared timer.
flock -u 9
exec 9>&-
python3 server/retention/install_retention.py --config server/retention/app.json --service oasis-update.service
systemctl daemon-reload
systemctl enable --now oasis-backup.timer
if [[ "$was_active" == true ]]; then systemctl start oasis-update.timer; fi
echo 'Installed oasis runtime and automatic image retention; existing app timer state preserved. For first setup, prepare HTTPS route then enable --now oasis-update.timer.'
