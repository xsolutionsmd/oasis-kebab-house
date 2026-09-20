import json,sqlite3
from pathlib import Path
from backup import backup
from server import create_app
def test_consistent_backup_restores_records_and_keys(tmp_path):
    live=tmp_path/'live';snap=tmp_path/'snapshot'
    a=create_app({'DATA_DIR':str(live),'TESTING':True,'OPERATOR_EMAIL':'original@example.test'})
    with a.db() as c:c.execute("INSERT INTO members(email,role) VALUES('added@example.test','viewer')")
    backup(live,snap)
    with a.db() as c:c.execute("DELETE FROM members WHERE email='added@example.test'")
    restored=create_app({'DATA_DIR':str(snap),'TESTING':True})
    with restored.db() as c:assert c.execute("SELECT role FROM members WHERE email='added@example.test'").fetchone()[0]=='viewer'
    assert (live/'encryption.key').read_bytes()==(snap/'encryption.key').read_bytes()
    assert (live/'secret.key').read_bytes()==(snap/'secret.key').read_bytes()
