"""Consistent SQLite snapshot plus the encryption/session keys. Never print keys."""
import os,sqlite3,shutil,sys,time
from pathlib import Path
def backup(source,destination):
    source=Path(source);destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    with sqlite3.connect(source/'oasis.sqlite3') as live,sqlite3.connect(destination/'oasis.sqlite3') as copy:
        live.backup(copy)
        assert copy.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    for name in ('secret.key','encryption.key'):shutil.copy2(source/name,destination/name)
    destination.chmod(0o700)
    for p in destination.iterdir():p.chmod(0o600)
    return destination
if __name__=='__main__':
    output=Path(sys.argv[1])/time.strftime('%Y%m%d-%H%M%S')
    backup(os.getenv('DATA_DIR','/data'),output)
    print('Consistent database and keys saved to',output)
