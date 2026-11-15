# SPDX-License-Identifier: GPL-3.0-only
"""Publish bounded, optional Discord RPC presence for the actual native process.

Only a public project Application ID is used. No authentication, messages,
island/save inspection, private Discord files, or sharing-setting changes.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time


def configuration(root: Path) -> dict:
    folder = root / "integration"
    result = json.loads((folder / "discord-presence.json").read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError("Unsupported Discord presence configuration.")
    local = folder / "discord-presence.local.json"
    if local.is_file():
        overrides = json.loads(local.read_text(encoding="utf-8"))
        if not isinstance(overrides, dict) or set(overrides) - {"enabled", "application_id"}:
            raise ValueError("Unsupported local Discord presence settings.")
        result.update(overrides)
    if not isinstance(result, dict) or result.get("schema") != 1 or type(result.get("enabled")) is not bool:
        raise ValueError("Unsupported Discord presence configuration.")
    app_id = result.get("application_id")
    if not isinstance(app_id, str) or (app_id and (not re.fullmatch(r"[0-9]{17,20}", app_id) or not 0 < int(app_id) < 2**64)):
        raise ValueError("Use a public numeric Discord Application ID.")
    return result


def activity(pid: int, started: int) -> dict:
    return {"pid": pid, "details": "Tomodachi Life: Living the Dream",
            "state": "Native Windows + ShareMii", "start": started}


class DiscordClient:
    """Own a pypresence client and its event loop on one worker thread."""
    def __init__(self, app_id):
        from pypresence import Presence, ActivityType

        class BoundedPresence(Presence):
            def connect(self):
                # pypresence's connection timeout covers opening the pipe;
                # explicitly bound its otherwise-unbounded handshake reads too.
                self.loop.run_until_complete(asyncio.wait_for(self.handshake(), timeout=2.0))

        self.kind = ActivityType.PLAYING
        self.client = BoundedPresence(app_id, loop=asyncio.new_event_loop(),
                                      connection_timeout=2.0, response_timeout=2.0)

    def connect(self):
        self.client.connect()

    def publish(self, payload):
        self.client.update(activity_type=self.kind, **payload)

    def clear(self, pid):
        self.client.clear(pid=pid)

    def close(self):
        try:
            self.client.close()
        finally:
            if not self.client.loop.is_closed():
                self.client.loop.close()


class GamePresence:
    def __init__(self, root, factory=DiscordClient, retry=5.0, refresh=30.0):
        self.root = Path(root)
        self.factory, self.retry, self.refresh = factory, retry, refresh
        self.stop_event = threading.Event()
        self.thread = None
        self.game_pid = None
        self.last_state = None

    def status(self, state):
        if state == self.last_state:
            return
        self.last_state = state
        path = self.root / "integration/discord-presence-status.json"
        temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
        try:
            temporary.write_text(json.dumps({"schema": 1, "status": state,
                                            "launcher_pid": os.getpid(), "game_pid": self.game_pid}), encoding="utf-8")
            temporary.replace(path)
        except OSError:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass  # a diagnostic failure must never prevent normal play

    def start(self, pid):
        self.game_pid = pid
        try:
            config = configuration(self.root)
        except (OSError, ValueError, TypeError):
            self.status("invalid_configuration")
            return
        if not config["enabled"]:
            self.status("disabled")
            return
        if not config["application_id"]:
            self.status("missing_application_id")
            return
        self.status("connecting")
        self.thread = threading.Thread(target=self.run, args=(config["application_id"], int(time.time())),
                                       name="Discord game presence", daemon=True)
        self.thread.start()

    def run(self, app_id, started):
        while not self.stop_event.is_set():
            client, published = None, False
            try:
                client = self.factory(app_id)
                client.connect()
                if self.stop_event.is_set():
                    return
                client.publish(activity(self.game_pid, started))
                published = True
                self.status("connected")
                while not self.stop_event.wait(self.refresh):
                    client.publish(activity(self.game_pid, started))
            except ImportError:
                self.status("missing_dependency")
                return
            except Exception as error:
                # Avoid logging raw IPC replies (which may include account data).
                if type(error).__name__ == "InvalidID":
                    self.status("invalid_application_id")
                    return
                self.status("waiting_for_discord")
            finally:
                if client is not None:
                    try:
                        if published:
                            client.clear(self.game_pid)
                    except Exception:
                        pass
                    try:
                        client.close()
                    except Exception:
                        pass
            if self.stop_event.wait(self.retry):
                break
        self.status("stopped")

    def stop(self):
        self.stop_event.set()
        if self.thread is not None:
            # Discord can be closed/unresponsive. Never hold up game shutdown
            # or a save-import reload; process-bound RPC also clears on exit.
            self.thread.join(timeout=1.0)


class NativeRunner:
    """Observe only the pinned upstream native subprocess.run call.

    Keep stdlib subprocess untouched for every other module/command. Unsupported
    call signatures delegate normally, so presence cannot break future launches.
    """
    def __init__(self, root, delegate=subprocess, presence_factory=GamePresence):
        self.root, self.delegate, self.presence_factory = Path(root), delegate, presence_factory

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def run(self, command, *args, **kwargs):
        recognized = False
        try:
            executable = Path(command[0]).resolve()
            work = (self.root / "build/work").resolve()
            recognized = (isinstance(command, (list, tuple)) and executable.parent == work and
                          executable.name.lower() in ("tomodachi_play.exe", "tomodachi_sharemii.exe") and
                          not args and not (set(kwargs) - {"cwd", "env", "stdout", "stderr"}))
        except (OSError, TypeError, IndexError):
            pass
        if not recognized:
            return self.delegate.run(command, *args, **kwargs)
        with self.delegate.Popen(command, **kwargs) as process:
            presence = None
            try:
                try:
                    presence = self.presence_factory(self.root)
                    presence.start(process.pid)
                except Exception:
                    pass  # optional Discord setup must never prevent the game
                return self.delegate.CompletedProcess(command, process.wait())
            finally:
                if presence is not None:
                    try:
                        presence.stop()
                    except Exception:
                        pass
