#!/usr/bin/env python3
"""Root-only consistent database/key/runtime backup, serialized with deployments."""
import fcntl,os,sqlite3,shutil,tarfile,tempfile,time
from pathlib import Path
def main():
    if os.geteuid()!=0:raise SystemExit('Run as root')
    state=Path('/var/lib/oasis-abdul-dev-deploy');root=Path('/opt/oasis-abdul-dev')
    with (state/'update.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if not (state/'current.json').is_file() or not (root/'data/oasis.sqlite3').is_file():
            print('No initialized release to back up yet');return
        if (state/'transaction').exists():raise SystemExit('Deployment recovery is pending; preserve evidence first')
        with tempfile.TemporaryDirectory(prefix='backup-',dir=state) as tmp:
            tmp=Path(tmp);data=tmp/'data';data.mkdir()
            with sqlite3.connect(root/'data/oasis.sqlite3') as live,sqlite3.connect(data/'oasis.sqlite3') as copy:
                live.backup(copy)
                assert copy.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            for name in ('secret.key','encryption.key'):shutil.copy2(root/'data'/name,data/name)
            for name in ('runtime.env','release.env','compose.yaml'):shutil.copy2(root/name,tmp/name)
            shutil.copy2(state/'current.json',tmp/'current.json')
            dest=state/'backups';dest.mkdir(exist_ok=True,mode=0o700)
            target=dest/('daily-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'.tar.gz')
            with tarfile.open(target,'w:gz') as archive:
                for p in tmp.iterdir():archive.add(p,arcname=p.name)
            target.chmod(0o600)
            print(target)
if __name__=='__main__':main()
