#!/usr/bin/env bash
# Reviewed, root-owned installation code. Release downloads are JSON data only.
set -euo pipefail
umask 077
[[ $EUID == 0 ]] || { echo 'Run the installed updater as root.' >&2; exit 1; }
repo=xsolutionsmd/oasis-kebab-house
root=/opt/oasis-derek-preview
state=/var/lib/oasis-derek-preview-deploy
mkdir -p "$state"
exec 9>"$state/update.lock"
flock -n 9 || exit 0
[[ ! -e "$state/transaction" ]] || { echo "Interrupted deployment requires inspection: $state/transaction. No new release applied." >&2; exit 1; }
work=$(mktemp -d "$state/check.XXXXXX")
candidate="oasis-derek-preview-candidate-$$"
deployment_started=false
committed=false
had_previous=false
had_current=false
compose=(docker compose --project-name oasis-derek-preview --project-directory "$root" --env-file "$root/release.env" -f "$root/compose.yaml")
next_compose=(docker compose --project-name oasis-derek-preview --project-directory "$root" --env-file "$work/next.env" -f "$work/next-compose.yaml")
rollback() {
  if [[ "$had_previous" == true ]]; then
    cp "$work/previous-compose.yaml" "$root/compose.yaml" || return 1
    cp "$work/previous.env" "$root/release.env" || return 1
    "${compose[@]}" up -d --no-build --wait --wait-timeout 90 || return 1
  else
    "${next_compose[@]}" rm --stop --force web || return 1
    rm -f -- "$root/compose.yaml" "$root/release.env" || return 1
  fi
  if [[ "$had_current" == true ]]; then
    cp "$work/previous-current.json" "$state/current.json.new" || return 1
    mv "$state/current.json.new" "$state/current.json" || return 1
  else
    rm -f -- "$state/current.json" "$state/current.json.new" || return 1
  fi
}
cleanup() {
  status=$?
  trap - EXIT
  trap '' TERM INT
  recovered=true
  if [[ "$deployment_started" == true && "$committed" != true ]]; then
    if ! rollback; then
      recovered=false
      status=1
      echo "Automatic recovery failed; recovery files retained in $work. Inspect oasis-derek-preview-update.service." >&2
    fi
  fi
  docker rm -f -v "$candidate" >/dev/null 2>&1 || true
  if [[ "$recovered" == true ]]; then
    # Clear the guard only after commit or successful recovery; retain it on failure.
    rm -f -- "$state/transaction"
    rm -rf -- "$work"
  fi
  exit "$status"
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
current_preview() { timeout 30 git ls-remote "https://github.com/$repo.git" refs/heads/derek-preview | cut -f1; }
preview=$(current_preview)
[[ "$preview" =~ ^[0-9a-f]{40}$ ]] || { echo 'Cannot determine current derek-preview revision.' >&2; exit 1; }
status=$(curl -LsS --connect-timeout 15 --max-time 60 --retry 2 -w '%{http_code}' \
  "https://github.com/$repo/releases/download/derek-preview-$preview/deployment.json?check=$(date +%s)" -o "$work/deployment.json")
if [[ "$status" == 404 ]]; then echo 'Current derek-preview is still building; retaining the existing application.'; exit 0; fi
[[ "$status" == 200 ]] || { echo "Release download failed (HTTP $status)." >&2; exit 1; }
mapfile -t release < <(python3 - "$work/deployment.json" <<'PY'
import json,re,sys
from pathlib import Path
p=Path(sys.argv[1])
if p.stat().st_size >= 4096: raise ValueError('Oversized manifest')
d=json.loads(p.read_text())
if not isinstance(d,dict) or set(d) != {'revision','image'}: raise ValueError('Invalid manifest fields')
if not isinstance(d['revision'],str) or not re.fullmatch(r'[0-9a-f]{40}',d['revision']): raise ValueError('Invalid revision')
if not isinstance(d['image'],str) or not re.fullmatch(r'ghcr\.io/xsolutionsmd/oasis\-kebab\-house\-derek\-preview@sha256:[0-9a-f]{64}',d['image']): raise ValueError('Invalid image')
print(d['revision']); print(d['image'])
PY
)
[[ ${#release[@]} == 2 ]] || { echo 'Invalid release manifest.' >&2; exit 1; }
revision=${release[0]}
image=${release[1]}
[[ "$revision" == "$preview" ]] || { echo 'Waiting for the current derek-preview release.'; exit 0; }
if [[ -f "$state/current.json" ]] && python3 - "$state/current.json" "$revision" "$image" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
sys.exit(d.get('revision') != sys.argv[2] or d.get('image') != sys.argv[3])
PY
then
  echo "Release $revision is already applied."
  exit 0
fi
docker network inspect xsolutions-proxy >/dev/null
docker pull "$image"
[[ $(docker image inspect "$image" --format '{{.Architecture}}') == arm64 ]]
[[ $(docker image inspect "$image" --format '{{.Os}}') == linux ]]
[[ $(docker image inspect "$image" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}') == "$revision" ]]
[[ $(docker image inspect "$image" --format '{{index .Config.Labels "org.opencontainers.image.source"}}') == "https://github.com/$repo" ]]
# The stateless candidate gets no production mounts, credentials or proxy alias.
docker run -d --name "$candidate" --read-only --tmpfs /tmp --tmpfs /data --tmpfs /config -p 127.0.0.1::8080 "$image"
port=$(docker port "$candidate" 8080/tcp | awk -F: '{print $NF}')
[[ "$port" =~ ^[0-9]+$ ]]
ready=false
for attempt in $(seq 1 30); do
  if [[ $(docker inspect "$candidate" --format '{{.State.Health.Status}}') == healthy ]]; then ready=true; break; fi
  sleep 1
done
[[ "$ready" == true ]]
actual=$(curl -fsS --max-time 10 "http://127.0.0.1:$port/version.json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["revision"])')
[[ "$actual" == "$revision" ]]
curl -fsS --max-time 10 "http://127.0.0.1:$port/" -o "$work/candidate.body"
grep -q 'A taste of' "$work/candidate.body"
curl -fsS --max-time 10 "http://127.0.0.1:$port/menu.html" -o "$work/candidate-menu.body"
grep -q 'The Oasis' "$work/candidate-menu.body"
docker rm -f -v "$candidate" >/dev/null
[[ "$revision" == "$(current_preview)" ]] || { echo 'Newer derek-preview exists; retaining current application.'; exit 0; }
if [[ -f "$root/compose.yaml" && -f "$root/release.env" ]]; then
  had_previous=true
  cp "$root/compose.yaml" "$work/previous-compose.yaml"
  cp "$root/release.env" "$work/previous.env"
elif [[ -e "$root/compose.yaml" || -e "$root/release.env" ]]; then
  echo 'Incomplete existing installation; repair before updating.' >&2
  exit 1
elif [[ -n $(docker ps -aq --filter label=com.docker.compose.project=oasis-derek-preview) ]]; then
  echo 'App containers exist without recovery configuration; repair before updating.' >&2
  exit 1
fi
if [[ -f "$state/current.json" ]]; then
  cp "$state/current.json" "$work/previous-current.json"
  had_current=true
fi
cp /usr/local/share/oasis-derek-preview/compose.yaml "$work/next-compose.yaml"
printf 'APP_IMAGE=%s\n' "$image" > "$work/next.env"
"${next_compose[@]}" config --quiet
# Durable refusal guard prevents a later tick overwriting evidence after SIGKILL/reboot.
printf '%s\n' "$work" > "$state/transaction"
sync -f "$state/transaction"
deployment_started=true
cp "$work/next-compose.yaml" "$root/compose.yaml"
cp "$work/next.env" "$root/release.env"
"${compose[@]}" up -d --no-build --wait --wait-timeout 90
verified=false
for attempt in $(seq 1 30); do
  actual=$(curl -fsS --max-time 10 --resolve oasis-derek.xsolutionsmd.com:443:127.0.0.1 \
    https://oasis-derek.xsolutionsmd.com/version.json | python3 -c 'import json,sys; print(json.load(sys.stdin)["revision"])') || actual=''
  if [[ "$actual" == "$revision" ]] \
    && curl -fsS --max-time 10 --resolve oasis-derek.xsolutionsmd.com:443:127.0.0.1 https://oasis-derek.xsolutionsmd.com/ -o "$work/live.body" \
    && grep -q 'A taste of' "$work/live.body"; then verified=true; break; fi
  sleep 2
done
[[ "$verified" == true ]]
if [[ "$had_previous" == true ]]; then
  cp "$work/previous-compose.yaml" "$state/previous-compose.yaml"
  cp "$work/previous.env" "$state/previous.env"
  if [[ "$had_current" == true ]]; then cp "$work/previous-current.json" "$state/previous-current.json"; fi
fi
cp "$work/deployment.json" "$state/current.json.new"
mv "$state/current.json.new" "$state/current.json"
sync -f "$state/current.json"
committed=true
echo "Deployed and verified $revision ($image)."
