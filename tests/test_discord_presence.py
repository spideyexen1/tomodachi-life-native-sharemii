# SPDX-License-Identifier: GPL-3.0-only
import asyncio
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "payload"))
import discord_presence as discord


class FakeClient:
    def __init__(self, events, published, fail=False):
        self.events, self.published, self.fail = events, published, fail

    def connect(self):
        self.events.append("connect")
        if self.fail:
            raise OSError("Discord unavailable")

    def publish(self, payload):
        self.events.append(("publish", payload))
        self.published.set()

    def clear(self, pid):
        self.events.append(("clear", pid))

    def close(self):
        self.events.append("close")


class PresenceLifecycle(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "integration").mkdir()
        self.config = self.root / "integration/discord-presence.json"
        self.write_config()

    def write_config(self, **changes):
        self.config.write_text(json.dumps({"schema": 1, "enabled": True,
                                          "application_id": "123456789012345678", **changes}))

    def test_publish_and_clear_use_actual_game_pid_without_private_data(self):
        events, sent = [], threading.Event()
        worker = discord.GamePresence(self.root, factory=lambda _: FakeClient(events, sent), refresh=60)
        worker.start(4242)
        self.assertTrue(sent.wait(1))
        worker.stop()
        self.assertEqual(events[0], "connect")
        payload = next(event[1] for event in events if isinstance(event, tuple) and event[0] == "publish")
        self.assertEqual(set(payload), {"pid", "details", "state", "start"})
        self.assertEqual(payload["pid"], 4242)
        self.assertLessEqual(abs(payload["start"] - time.time()), 5)
        self.assertIn(("clear", 4242), events)
        self.assertEqual(events[-1], "close")
        self.assertFalse(worker.thread.is_alive())
        status = json.loads((self.root / "integration/discord-presence-status.json").read_text())
        self.assertEqual(status["status"], "stopped")

    def test_reconnect_when_discord_opens_later(self):
        events, sent, attempts = [], threading.Event(), []
        def factory(_):
            attempts.append(1)
            return FakeClient(events, sent, fail=len(attempts) == 1)
        worker = discord.GamePresence(self.root, factory=factory, retry=0.01, refresh=60)
        worker.start(4242)
        self.assertTrue(sent.wait(1))
        worker.stop()
        self.assertEqual(len(attempts), 2)
        self.assertEqual(events[:3], ["connect", "close", "connect"])

    def test_disabled_unconfigured_and_missing_dependency_do_not_block(self):
        for changes, expected in (({"enabled": False}, "disabled"), ({"application_id": ""}, "missing_application_id")):
            self.write_config(**changes)
            factory = Mock(side_effect=AssertionError("must not connect"))
            worker = discord.GamePresence(self.root, factory=factory)
            worker.start(4242)
            self.assertEqual(worker.last_state, expected)
            self.assertIsNone(worker.thread)
            factory.assert_not_called()
        self.write_config()
        worker = discord.GamePresence(self.root, factory=Mock(side_effect=ImportError("not installed")))
        worker.start(4242)
        worker.thread.join(1)
        self.assertEqual(worker.last_state, "missing_dependency")
        self.assertFalse(worker.thread.is_alive())

    def test_local_opt_out_survives_global_config_updates(self):
        local = self.root / "integration/discord-presence.local.json"
        local.write_text('{"enabled":false}')
        self.write_config(application_id="223456789012345678")
        self.assertFalse(discord.configuration(self.root)["enabled"])
        self.assertEqual(local.read_text(), '{"enabled":false}')

    def test_invalid_ids_and_malformed_configs_are_refused(self):
        for app_id in ("token-value", 123456789012345678, "18446744073709551616"):
            self.write_config(application_id=app_id)
            with self.assertRaises(ValueError):
                discord.configuration(self.root)
        self.config.write_text("[]")
        worker = discord.GamePresence(self.root)
        worker.start(4242)
        self.assertEqual(worker.last_state, "invalid_configuration")

    def test_missing_status_directory_does_not_break_worker(self):
        worker = discord.GamePresence(self.root / "missing")
        worker.start(4242)
        self.assertEqual(worker.last_state, "invalid_configuration")


class NativeProcessObserver(unittest.TestCase):
    def test_actual_native_launch_lifecycle_and_nonzero_exit_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            process = Mock(pid=4242)
            process.wait.return_value = 7
            context = Mock()
            context.__enter__ = Mock(return_value=process)
            context.__exit__ = Mock(return_value=False)
            delegate = Mock()
            delegate.Popen.return_value = context
            delegate.CompletedProcess = subprocess.CompletedProcess
            presence = Mock()
            runner = discord.NativeRunner(root, delegate, lambda _: presence)
            command = [str(root / "build/work/tomodachi_play.exe"), "main.elf", "0"]
            result = runner.run(command, cwd=str(root / "build/work"), stdout="log", stderr=subprocess.STDOUT)
            self.assertEqual(result.returncode, 7)
            self.assertEqual(result.args, command)
            presence.start.assert_called_once_with(4242)
            presence.stop.assert_called_once()
            delegate.run.assert_not_called()

    def test_other_programs_and_unsupported_run_options_delegate_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, delegate, factory = Path(temporary), Mock(), Mock()
            runner = discord.NativeRunner(root, delegate, factory)
            commands = (["another.exe"], [str(root / "elsewhere/tomodachi_play.exe")],
                        [str(root / "build/work/tomodachi_play.exe")])
            for command in commands:
                options = {"check": True} if command is commands[-1] else {}
                self.assertIs(runner.run(command, **options), delegate.run.return_value)
                delegate.run.assert_called_with(command, **options)
            factory.assert_not_called()
            delegate.Popen.assert_not_called()

    def test_discord_failures_cannot_change_game_exit_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, process, delegate = Path(temporary), Mock(pid=4242), Mock()
            process.wait.return_value = 0
            context = Mock()
            context.__enter__ = Mock(return_value=process)
            context.__exit__ = Mock(return_value=False)
            delegate.Popen.return_value = context
            delegate.CompletedProcess = subprocess.CompletedProcess
            presence = Mock()
            presence.start.side_effect = RuntimeError("optional integration failed")
            presence.stop.side_effect = RuntimeError("optional cleanup failed")
            runner = discord.NativeRunner(root, delegate, lambda _: presence)
            result = runner.run([str(root / "build/work/tomodachi_sharemii.exe")])
            self.assertEqual(result.returncode, 0)
            presence.stop.assert_called_once()


class RealDependencyAdapter(unittest.TestCase):
    def test_unresponsive_handshake_is_bounded_and_uses_owned_loop(self):
        from pypresence import Presence
        real_wait_for = asyncio.wait_for
        async def unresponsive(_):
            await asyncio.sleep(60)
        def short_wait(awaitable, timeout):
            self.assertEqual(timeout, 2.0)
            return real_wait_for(awaitable, timeout=0.01)
        client = discord.DiscordClient("123456789012345678")
        try:
            with patch.object(Presence, "handshake", unresponsive), patch.object(discord.asyncio, "wait_for", short_wait):
                with self.assertRaises(TimeoutError):
                    client.connect()
            self.assertFalse(client.client.loop.is_running())
        finally:
            client.client.loop.close()
            asyncio.set_event_loop(None)

    def test_release_has_shared_public_application_id_enabled(self):
        payload = Path(__file__).resolve().parents[1] / "payload/discord-presence.json"
        config = json.loads(payload.read_text(encoding="utf-8"))
        self.assertIs(config["enabled"], True)
        self.assertEqual(config["application_id"], "1571541052223918080")


if __name__ == "__main__":
    unittest.main()
