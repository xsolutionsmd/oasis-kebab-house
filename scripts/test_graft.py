"""Real Git fixtures: no network, Docker or private data required."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('graft_adapter', Path(__file__).with_name('graft.py'))
graft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graft)

class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        graft.ROOT = self.root
        self.git('init', '-b', 'dev')
        self.git('config', 'user.name', 'Context test')
        self.git('config', 'user.email', 'context@example.invalid')
        self.git('remote', 'add', 'origin', 'https://github.com/xsolutionsmd/test-context.git')
        self.write('tools/graft/context.json', json.dumps({'repository':'xsolutionsmd/test-context','sourcePatterns':['app/*.js']}))
        self.write('.gitignore', '.graft-context/\n.env\n')
        self.write('app/main.js', 'function original() { return 1; }\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.git('branch', 'main')
    def tearDown(self):
        self.temp.cleanup()
    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True).strip()
    def write(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    def test_wrong_ref_and_detached_and_remote(self):
        with self.assertRaisesRegex(ValueError, 'Expected branch main'): graft.identity('main')
        self.git('checkout', '--detach', '-q')
        with self.assertRaisesRegex(ValueError, 'detached'): graft.identity('dev')
        self.git('checkout', '-q', 'dev')
        self.git('remote', 'set-url', 'origin', 'https://github.com/wrong/repo.git')
        with self.assertRaisesRegex(ValueError, 'origin'): graft.identity('dev')
    def test_production_dirty_and_development_edits(self):
        self.write('app/main.js', 'function edited() {}')
        self.assertTrue(graft.identity('dev')[1]['dirty'])
        self.git('checkout', '-q', 'main')
        with self.assertRaisesRegex(ValueError, 'clean main'): graft.identity('main')
    def test_inventory_excludes_untracked_and_tracked_secrets(self):
        self.write('app/untracked.js', 'never index')
        self.write('.env', 'secret')
        self.write('app/config/secret.js', 'secret')
        self.write('private/secret.js', 'secret')
        self.write('archive/app/secret.js', 'secret')
        self.git('add', 'app/config/secret.js', 'private/secret.js', 'archive/app/secret.js')
        cfg, info = graft.identity('dev')
        self.assertEqual(graft.inventory(cfg), ['app/main.js'])
        cache = graft.snapshot(cfg, info)
        self.assertEqual(list((cache/'source').rglob('*.js')), [cache/'source/app/main.js'])
    def test_refresh_removal_and_branch_cache_isolation(self):
        cfg, info = graft.identity('dev')
        dev = graft.snapshot(cfg, info)
        self.write('app/main.js', 'function changedOnlyInDev() {}')
        graft.snapshot(cfg, info)
        self.assertIn('changedOnlyInDev', (dev/'source/app/main.js').read_text())
        self.git('checkout', '--', 'app/main.js')
        self.git('checkout', '-q', 'main')
        cfg, info = graft.identity('main')
        main = graft.snapshot(cfg, info)
        self.assertNotEqual(main, dev)
        self.assertNotIn('changedOnlyInDev', (main/'source/app/main.js').read_text())
        self.git('checkout', '-q', 'dev')
        self.git('rm', '-q', 'app/main.js')
        cfg, info = graft.identity('dev')
        graft.snapshot(cfg, info)
        self.assertFalse((dev/'source/app/main.js').exists())
        self.assertTrue((main/'source/app/main.js').exists())
    def test_cache_identity_poisoning_rejected(self):
        cfg, info = graft.identity('dev')
        cache = graft.snapshot(cfg, info)
        stamp = json.loads((cache/'identity.json').read_text())
        stamp['ref'] = 'main'
        (cache/'identity.json').write_text(json.dumps(stamp))
        with self.assertRaisesRegex(ValueError, 'identity mismatch'): graft.snapshot(cfg, info)
    def test_bad_inventory_schema_rejected(self):
        for patterns in ('app/*.js', [], [None], ['/outside/*.js']):
            self.write('tools/graft/context.json', json.dumps({'repository':'xsolutionsmd/test-context','sourcePatterns':patterns}))
            with self.assertRaisesRegex(ValueError, 'sourcePatterns'): graft.identity('dev')
    def test_changed_source_and_branch_after_snapshot_rejected(self):
        cfg, info = graft.identity('dev')
        cache = graft.snapshot(cfg, info)
        self.write('app/main.js', 'function raced() {}')
        with self.assertRaisesRegex(ValueError, 'Source changed'): graft.verify_snapshot(cfg, info, cache)
        self.git('checkout', '--', 'app/main.js')
        self.git('checkout', '-q', 'main')
        with self.assertRaisesRegex(ValueError, 'Expected branch'): graft.verify_snapshot(cfg, info, cache)
    def test_concurrent_query_lock_rejected_before_docker(self):
        self.write('.graft-context/dev.lock', '')
        with patch('sys.argv', ['graft.py', '--ref', 'dev', 'ask', 'original']):
            with self.assertRaisesRegex(ValueError, 'already in use'): graft.main()
    def test_whole_repository_text_and_infrastructure_coverage(self):
        self.write('tools/graft/context.json', json.dumps({'repository':'xsolutionsmd/test-context','sourcePatterns':['**']}))
        wanted=['Dockerfile','Dockerfile.dev','compose.yaml','.github/workflows/check.yml','.devcontainer/devcontainer.json','tools/graft/Dockerfile','server/install.sh','website.ps1','docs/OPERATIONS.md','app/index.html','app/style.css','Caddyfile']
        excluded=['.env','booking/config/google-client.json','oauth_tokens.json','client_secret.json','service-account.json','private/secret.js','data/customer.json','runtime/customer.json','logs/secret.json','models/data.json','node_modules/index.js','image.png','graft/cache.json']
        for name in wanted+excluded: self.write(name, 'whole-repository-probe')
        self.git('add', '-f', *wanted, *excluded)
        cfg, info=graft.identity('dev')
        files=graft.inventory(cfg)
        self.assertTrue(set(wanted).issubset(files))
        self.assertFalse(set(excluded).intersection(files))
        self.assertEqual(info['omittedUntracked'], [])
    def test_feature_context_is_explicit_and_separate(self):
        self.git('checkout', '-qb', 'feature/docker-work')
        with self.assertRaisesRegex(ValueError, 'Expected branch'): graft.identity('dev')
        cfg, info=graft.identity('dev', True)
        self.assertEqual(info['ref'], 'dev')
        self.assertEqual(info['branch'], 'feature/docker-work')
        self.assertTrue(info['cacheKey'].startswith('dev-feature-'))
        self.assertNotEqual(graft.snapshot(cfg, info), self.root/'.graft-context/dev')
        with self.assertRaisesRegex(ValueError, 'Feature context'): graft.identity('main', True)
        self.git('checkout', '-q', 'main')
        with self.assertRaisesRegex(ValueError, 'Feature context'): graft.identity('dev', True)
    def test_parent_symlink_cannot_expose_runtime(self):
        self.write('tools/graft/context.json', json.dumps({'repository':'xsolutionsmd/test-context','sourcePatterns':['**']}))
        self.write('alias/main.js', 'tracked placeholder')
        self.write('runtime/main.js', 'private runtime')
        self.git('add', 'alias/main.js')
        (self.root/'alias/main.js').unlink()
        (self.root/'alias').rmdir()
        try: (self.root/'alias').symlink_to(self.root/'runtime', target_is_directory=True)
        except OSError: self.skipTest('Directory symlinks require platform permission')
        cfg, _=graft.identity('dev')
        self.assertNotIn('alias/main.js', graft.inventory(cfg))
    def test_oversized_and_binary_text_names_excluded(self):
        (self.root/'app/large.js').write_bytes(b'x'*(graft.MAX_FILE_BYTES+1))
        (self.root/'app/binary.js').write_bytes(b'a\x00b')
        self.git('add', 'app/large.js', 'app/binary.js')
        cfg, _=graft.identity('dev')
        self.assertEqual(graft.inventory(cfg), ['app/main.js'])

if __name__ == '__main__': unittest.main()
