"""Launcher contract tests; no Docker daemon, database, or package downloads needed."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'scripts').mkdir()
        shutil.copy(Path(__file__).with_name('run'), self.root / 'scripts/run')
        self.bin = self.root / '.venv/bin'
        self.bin.mkdir(parents=True)
        self.log = self.root / 'calls'
        for name in ('docker',):
            path = self.bin / name
            path.write_text(
                '#!/bin/bash\n'
                'printf "%s" "${0##*/}" >> "$CALL_LOG"\n'
                'printf " <%s>" "$@" >> "$CALL_LOG"\n'
                'printf "\\n" >> "$CALL_LOG"\n'
                'if [[ "${FAIL_COMMAND:-}" == "${0##*/} $*" ]]; then exit 17; fi\n'
            )
            path.chmod(0o755)
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ('DATABASE_URL', 'PORT', 'HOST', 'LOG_LEVEL')}
        self.env.update(PATH=f'{self.bin}:/usr/bin:/bin', CALL_LOG=str(self.log))

    def run_mode(self, mode, **env):
        return subprocess.run(
            [str(self.root / 'scripts/run'), mode], cwd='/',
            env=self.env | env, capture_output=True, text=True,
        )

    def calls(self):
        return self.log.read_text() if self.log.exists() else ''

    def test_both_flavors_run_full_stack_from_any_directory(self):
        for mode in ('dev', 'prod'):
            with self.subTest(mode=mode):
                self.log.unlink(missing_ok=True)
                result = self.run_mode(mode)
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = self.calls().splitlines()
                self.assertEqual(len(calls), 2)
                self.assertEqual(calls[0], 'docker <compose> <version>')
                self.assertIn(f'<{self.root}/compose.yaml>', calls[1])
                self.assertIn('<up> <--build> <--force-recreate>', calls[1])
                self.assertEqual('compose.dev.yaml' in calls[1], mode == 'dev')

    def test_compose_failure_is_propagated(self):
        result = self.run_mode('dev', FAIL_COMMAND='docker compose version')
        self.assertEqual(result.returncode, 17)
        self.assertNotIn('<up>', self.calls())

    def test_start_failure_is_propagated(self):
        command = f'docker compose -f {self.root}/compose.yaml up --build --force-recreate'
        result = self.run_mode('prod', FAIL_COMMAND=command)
        self.assertEqual(result.returncode, 17)

    def test_help_and_removed_modes_have_no_side_effects(self):
        self.assertEqual(self.run_mode('--help').returncode, 0)
        for mode in ('migrate', 'unknown'):
            self.assertEqual(self.run_mode(mode).returncode, 2)
        self.assertEqual(self.calls(), '')


if __name__ == '__main__':
    unittest.main()
