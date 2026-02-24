"""Tests for wacht live reload server."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from wacht import ReloadServer, ReloadHandler, get_mtime, get_pid_file, __version__


class TestGetMtime(unittest.TestCase):
    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = get_mtime(tmp)
            self.assertEqual(result, {})

    def test_single_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test.txt").write_text("hello")
            result = get_mtime(tmp)
            self.assertIn("test.txt", result)
            self.assertIsInstance(result["test.txt"], int)

    def test_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.txt").write_text("a")
            Path(tmp, "b.txt").write_text("b")
            result = get_mtime(tmp)
            self.assertEqual(len(result), 2)
            self.assertIn("a.txt", result)
            self.assertIn("b.txt", result)


class TestGetPidFile(unittest.TestCase):
    def test_returns_path(self):
        pid_file = get_pid_file()
        self.assertIsInstance(pid_file, Path)
        self.assertTrue(pid_file.name.endswith(".pid"))

    def test_creates_directory(self):
        pid_file = get_pid_file()
        self.assertTrue(pid_file.parent.exists())


class TestReloadServer(unittest.TestCase):
    def test_init_defaults(self):
        server = ReloadServer()
        self.assertEqual(server.port, 8080)
        self.assertEqual(server.webroot, Path(".").resolve())

    def test_init_custom(self):
        with tempfile.TemporaryDirectory() as tmp:
            server = ReloadServer(port=3000, webroot=tmp)
            self.assertEqual(server.port, 3000)
            self.assertEqual(server.webroot, Path(tmp).resolve())

    def test_stop_no_pid_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["XDG_RUNTIME_DIR"] = tmp
            server = ReloadServer()
            with self.assertRaises(SystemExit) as cm:
                server.stop()
            self.assertEqual(cm.exception.code, 1)

    @patch("os.kill")
    @patch("sys.exit")
    def test_stop_success(self, mock_exit, mock_kill):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["XDG_RUNTIME_DIR"] = tmp
            pid_file = Path(tmp) / "wacht" / "wacht.pid"
            pid_file.parent.mkdir(parents=True, exist_ok=True)
            pid_file.write_text("12345")
            server = ReloadServer()
            server.stop()
            mock_kill.assert_called_once_with(12345, 15)  # SIGTERM = 15


class TestReloadHandler(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.handler = ReloadHandler.__new__(ReloadHandler)
        self.handler.webroot = Path(self.tmpdir)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmpdir)

    def test_translate_path(self):
        result = self.handler.translate_path("/index.html")
        self.assertIn("index.html", result)
        self.assertIn(self.tmpdir, result)

    def test_translate_path_traversal_blocked(self):
        result = self.handler.translate_path("/../etc/passwd")
        # Should be normalized - ".." removed, so it becomes /etc/passwd under webroot
        self.assertIn(self.tmpdir, result)
        # But shouldn't escape webroot - it should be within tmpdir
        self.assertTrue(result.startswith(self.tmpdir))


class TestIntegration(unittest.TestCase):
    def test_server_lifecycle(self):
        """Test basic server creation and attributes."""
        with tempfile.TemporaryDirectory() as tmp:
            server = ReloadServer(port=9999, webroot=tmp)
            self.assertIsNotNone(server._handler_factory)


class TestVersion(unittest.TestCase):
    def test_version_exists(self):
        self.assertIsInstance(__version__, str)
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+")


if __name__ == "__main__":
    unittest.main(verbosity=2)
