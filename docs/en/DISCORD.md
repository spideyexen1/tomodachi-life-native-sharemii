# Discord activity for every player

From **0.5.1**, setup includes compatibility with Discord's normal game detection. Launching from the ShareMii shortcut keeps the window title **Tomodachi Life: Living the Dream**, including during loading, so Discord no longer has to infer a name from a suffix such as `60 fps`.

Game registration is a personal Discord preference. The maintainer's account registration cannot be transferred to other players. Each player can register their own installation once, without tokens, bots, client mods or extra tools.

## First-time configuration

1. With the game closed, install/update using **Setup → Existing port**. For a new installation, see [the installation guide](INSTALL.md). Older installations must complete the update; repairing F1 settings alone does not rebuild this patch.
2. Open **Discord desktop** on your PC and launch the game using **Tomodachi Life - ShareMii** or **Tomodachi Life - Nativo + ShareMii**.
3. Open **User Settings → Registered Games → Add it!** in Discord.
4. Select **Tomodachi Life: Living the Dream** and choose **Add Game**. The launcher's running process is `tomodachi_play.exe`; if needed, check that it belongs to your installation.
5. For an old entry named `60 fps`, click the current game's name and rename it **Tomodachi Life: Living the Dream**, then click outside the field to confirm. Deleting the entry is unnecessary.
6. Check that detection is enabled for the game. Sharing it with others also depends on **Activity Privacy → Share my activity** and any per-server settings.
7. Open your profile card: while playing it should show **Playing Tomodachi Life: Living the Dream**. When the process exits, the current activity disappears; Registered Games may retain it as a recently played title.

This uses [Discord's documented manual registration](https://discord.com/blog/how-to-share-what-youre-playing-listening-to-or-watching-as-your-status-on-discord), subject to its [activity-sharing controls](https://support.discord.com/hc/en-us/articles/7931156448919-Activity-Sharing-on-Discord-FAQ). The browser/mobile client alone does not detect the local Windows game process.

## Troubleshooting

- Keep Discord desktop and the actual game open; setup or the launcher alone is insufficient.
- Use the updated ShareMii shortcut. Direct upstream diagnostic runs can retain frame/FPS titles.
- Check your personal and server activity-sharing preferences. Setup does not change them for you.
- After moving the installation, repeat **Add it!** with the new copy running if Discord no longer detects it.
- If the picker still offers `60 fps`, complete the port update and restart the game; an existing entry can be renamed as above.

## What the project ships

This updates the open-source runtime's window title and launcher arguments. It does not read Discord files/credentials, modify its client, access messages or automatically configure other accounts' sharing. Inclusion in Discord's official game catalog is controlled by Discord; this compatibility does not promise global detection without first-time registration.

The patch targets the SHA-256-verified supported runtime v1.0.3 and preserves the original source at `runtime/display.upstream.c`. FPS measurements/logs remain; diagnostic launches without `TOMO_DISCORD_TITLE` keep dynamic titles. Saves, input, audio and rendering are unchanged. No game content is distributed.
