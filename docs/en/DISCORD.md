# Automatic Discord activity

Setup **0.6.0** adds local Discord Rich Presence for every installation. Players do not need to create a developer application, enter an ID, sign in through this integration, or use **Registered Games → Add it!**.

## Use it

1. Close the game and install 0.6.0 or later. For an existing installation, select **Existing port** in setup.
2. Open **Discord desktop** on the same PC and launch using **Tomodachi Life - ShareMii** or **Tomodachi Life - Nativo + ShareMii**.
3. Once the actual native game starts, the profile activity shows the app **Tomodachi Life Native + ShareMii**, details **Tomodachi Life: Living the Dream**, **Native Windows + ShareMii** and elapsed time.
4. Closing the native game removes its Rich Presence. An automatic import reload ends the old session and starts a new one.

Discord may also be opened after the game: the launcher retries while the game is running. Reconnecting after a Discord restart can take roughly 30–40 seconds. The browser/mobile client alone cannot receive the local Windows IPC connection. The setup or launcher window alone does not publish activity.

Visibility still follows your own [Discord activity-sharing preferences](https://support.discord.com/hc/en-us/articles/7931156448919-Activity-Sharing-on-Discord-FAQ). The integration does not change these settings.

## If it does not appear

- Use the ShareMii shortcut, keep Discord desktop running, and allow time for reconnection.
- Check `integration/discord-presence-status.json` inside your installation. `connected` means Discord acknowledged the activity; visibility remains controlled by Discord. `waiting_for_discord` means the local client is unavailable. `missing_dependency` means rerun setup. `invalid_application_id` or `invalid_configuration` means reinstall the project's default configuration. This diagnostic can be stale if the launcher was terminated abruptly.
- Discord being absent, closed or unresponsive does not prevent the game from starting or exiting. Other activities may affect what your profile displays.
- The stable game window title from 0.5.1 remains for standard detection, but manual registration is not required for Rich Presence.

## Disable locally

Create `integration/discord-presence.local.json` containing:

```json
{"enabled": false}
```

Restart the game. This local override is preserved by integration updates. Set it to `true` to enable again. A custom public `application_id` may also be supplied there; never enter a bot token, client secret or password.

## Implementation and privacy

The shared public Application ID is `1571541052223918080`, in `integration/discord-presence.json`. The setup installs pinned `pypresence==4.6.2` in the port's private Python environment. The launcher uses Discord's local IPC protocol and the actual native game PID, with bounded connection attempts and a background reconnect worker. It publishes only the fixed game/project labels and session start time. It does not read islands, saves, Mii names, messages, Discord account files or credentials. The local status file contains only status and process IDs; raw IPC replies are not logged.

This follows Discord's [Rich Presence without authentication](https://docs.discord.com/developers/discord-social-sdk/development-guides/setting-rich-presence) and [SET_ACTIVITY RPC](https://docs.discord.com/developers/topics/rpc#commands-setactivity) documentation. It does not add the game to Discord's official detection catalog. Local testing verified the activity and its removal using a separate test island; fake-client tests cover late connections, optional failures and process cleanup.
