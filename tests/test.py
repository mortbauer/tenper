import subprocess
import unittest

from mock import patch

import tenper


class TenperTests(unittest.TestCase):
    def test_command_list(self):
        self.assertEqual(
            tenper.command_list('ls'),
            ['ls'])

        self.assertEqual(
            tenper.command_list('ls /'),
            ['ls', '/'])

        self.assertEqual(
            tenper.command_list('echo {message}', message='Hello, world.'),
            ['echo', 'Hello, world.'])

    def test_run(self):
        with patch('subprocess.call') as call:
            tenper.run('ls /')
            call.assert_called_once_with(['ls', '/'])

        with patch('subprocess.call') as call:
            tenper.run(
                'tmux new-window -t {session} -n {window}',
                session='some thing',
                window='hi')
            call.assert_called_once_with(
                ['tmux', 'new-window', '-t', 'some thing', '-n', 'hi'])

    def test_parse_args(self):
        f, a = tenper.parse_args(['-l'])
        self.assertEqual(f, tenper.list_envs)
        self.assertEqual(a, [])

        f, a = tenper.parse_args(['--edit', 'foo'])
        self.assertEqual(f, tenper.edit)
        self.assertEqual(a, ['foo'])

        f, a = tenper.parse_args(['--delete', 'foo'])
        self.assertEqual(f, tenper.delete)
        self.assertEqual(a, ['foo'])

        f, a = tenper.parse_args(['--rebuild', 'bar'])
        self.assertEqual(f, tenper.rebuild)
        self.assertEqual(a, ['bar'])

        f, a = tenper.parse_args(['foobar'])
        self.assertEqual(f, tenper.start)
        self.assertEqual(a, ['foobar'])

        with self.assertRaises(Exception):
            tenper.parse_args([])

        with self.assertRaises(Exception):
            tenper.parse_args(['-e'])
