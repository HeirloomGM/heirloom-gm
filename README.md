<p align="center">
  <img src="https://github.com/HeirloomGM/heirloom-gm/raw/main/docs/images/heirloom.png" alt="Heirloom Games Manager" width="260">
</p>

<h1 align="center">Heirloom Games Manager</h1>

<p align="center">
  A Linux-friendly command line tool and Python library for downloading, installing, tracking, launching, and uninstalling games from <a href="https://www.legacygames.com">Legacy Games</a>.
</p>

<p align="center">
  Built with the Steam Deck in mind.
</p>

---

## What Is This?

Heirloom Games Manager is a small but increasingly serious tool for accessing your Legacy Games library on Linux. Legacy Games does not currently provide a Linux version of its installation manager, which is a little awkward if you are trying to enjoy those games on a Steam Deck, a living room Linux box, or just a regular desktop where you would rather not boot Windows for one installer.

Heirloom fills that gap. It can log in to Legacy Games, list your library, download installers, install games through Wine or 7-Zip extraction, keep track of what is installed, launch installed games, and uninstall games it manages. You can use it as a CLI, import it as a Python library, or run the Qt 6 QML interface.

It is inspired by projects like [legendary](https://github.com/derrod/legendary) for Epic Games and [nile](https://github.com/imLinguin/nile) for Amazon Games. Legacy -> Heirloom. The joke was right there. I had to.

## Background

I love my [Steam Deck](https://store.steampowered.com/steamdeck). Most of all, I love tinkering with it and seeing how many of my multitudinous games I can get running on it.

[Heroic](https://heroicgameslauncher.com) does a great job with Epic, GOG, and Amazon Prime Gaming. But every now and then, an Amazon Prime Gaming giveaway shows up through a not-so-well-known store called Legacy Games. Those games are perfectly real, perfectly playable little treasures, but getting them onto Linux is more manual than it should be.

So I made Heirloom. It started as a rough command line helper, and it is gradually becoming a proper little game manager: safer, faster, more predictable, and less held together by hope and shell fumes.

## Current Features

- Log in to Legacy Games and read your game library.
- List all games, installed games, or not-yet-installed games.
- Download game installers with progress display.
- Install games using Wine or 7-Zip.
- Track installed games in a local SQLite database.
- Remember install directories and launch executables.
- Launch installed games through Wine.
- Uninstall managed games with path-safety checks.
- Detect manually removed install folders and mark them as not installed.
- Store configuration in `~/.config/heirloom/config.ini`.
- Encrypt stored passwords using a locally generated key.
- Fall back gracefully when a desktop keyring backend is not available.
- Provide a Python library API for other tools and frontends.
- Provide a Qt 6 QML desktop interface via `heirloom-gui`.

The GUI is intentionally built on the same library and local database as the CLI. That keeps the pretty part honest.

## Recent Improvements

Heirloom has been getting some much-needed grown-up plumbing:

- CLI startup is lazier now, so importing the CLI or asking for help does not immediately log in, refresh the library, and open the database.
- Downloads use a persistent HTTP session, request timeouts, larger streaming chunks, and HTTP error checks.
- Install paths are handled with `pathlib` instead of fragile string concatenation.
- The install database now uses parameterized SQL queries.
- Library refreshes preserve existing install records instead of trampling them.
- Uninstall now removes only directories under the configured install root.
- Uninstall resets install state instead of deleting the game record from the local catalog.
- Password handling supports the original keyring entry, a newer keyring entry, and a local encrypted-key fallback for Linux systems without a working keyring.
- Encrypted passwords that cannot be decrypted now fail with a clear local error instead of being sent to Legacy Games and producing a confusing server error.
- The old experimental GUI work has been replaced with a PySide6/QML application shell.
- GUI library loading, installation, and uninstall operations run off the UI thread.
- The GUI now has a setup flow, artwork cache, search, installed/not-installed filters, responsive cards, and launch/install/uninstall actions.
- Focused unit tests now cover path conversion, install-state database behavior, quoted game names, and CLI import behavior.

## Requirements

Heirloom requires Python 3.10 or newer.

Runtime dependencies:

```text
requests
typer
rich
InquirerPy
cryptography
keyring
PySide6
```

For installing and launching games, you will also want:

- `wine`, for running Windows installers and games.
- `7z`, if you prefer extraction-based installs where possible.

On Steam Deck, those pieces may depend on how you have set up your environment. Heirloom does not try to manage Wine prefixes yet; it assumes you know where you want games installed and which Wine executable you want to use.

## Installation

For a local checkout, the easiest route is:

```bash
./install.sh
```

That script creates `.venv` in the repository, installs the requirements, installs Heirloom itself from `pyproject.toml`, and creates a KDE application-menu entry called `Heirloom GUI` under Games. The menu item runs `run-heirloom-gui.sh`, which activates the virtual environment and launches the GUI.

I usually work in a virtual environment:

```bash
python3 -m venv ~/heirloom.venv
source ~/heirloom.venv/bin/activate
pip install git+https://github.com/heirloom-gm/heirloom-gm
```

This installs the CLI as:

```bash
heirloom-gm
```

And the Qt GUI as:

```bash
heirloom-gui
```

## Configuration

On first run, Heirloom prompts for:

- Legacy Games username or email.
- Legacy Games password.
- Base install directory, such as `~/Games/LegacyGames/`.
- Path to `wine`.
- Path to `7z`.
- Default installation method.

The CLI stores configuration at:

```text
~/.config/heirloom/config.ini
```

Installed-game state is stored separately in:

```text
~/.config/heirloom/games.db
```

Passwords are encrypted before being written to the config file. The encryption key is stored in the system keyring when available. If keyring is not available, Heirloom uses a local fallback key file under `~/.config/heirloom/` with user-only permissions.

Do not commit local config files or credentials. Seriously. Future you deserves peace.

To throw away the saved configuration and enter credentials/settings again:

```bash
heirloom-gm --reconfigure
```

The GUI supports the same reset flow:

```bash
heirloom-gui --reconfigure
```

Reconfiguration removes `~/.config/heirloom/config.ini`. It does not remove `~/.config/heirloom/games.db`, so your local installed-game records are preserved.

## CLI Usage

### List Games

```bash
heirloom-gm list
```

Only installed games:

```bash
heirloom-gm list --installed
```

Only games not currently recorded as installed:

```bash
heirloom-gm list --not-installed
```

### Show Game Info

```bash
heirloom-gm info
```

Or provide a game directly:

```bash
heirloom-gm info --game "The Wild Case"
```

### Download A Game

```bash
heirloom-gm download --game "The Wild Case"
```

Example output:

```text
Downloading The Wild Case (218.1 MB) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
Successfully downloaded The Wild Case setup executable as TheWildCase_N28M1FX.exe
```

### Install A Game

Use the configured default install method:

```bash
heirloom-gm install --game "The Wild Case"
```

Force a specific install method:

```bash
heirloom-gm install --game "The Wild Case" --install-method wine
heirloom-gm install --game "The Wild Case" --install-method 7zip
```

After installation, Heirloom records the install directory and tries to identify the most likely launch executable. If more than one plausible executable is found, it asks you to pick one.

### Launch A Game

```bash
heirloom-gm launch --game "The Wild Case"
```

### Uninstall A Game

```bash
heirloom-gm uninstall --game "The Wild Case"
```

For non-interactive use:

```bash
heirloom-gm uninstall --game "The Wild Case" --yes
```

Heirloom only removes install directories under the configured base install directory. That guardrail is intentional.

## GUI Usage

Launch the Qt interface with:

```bash
heirloom-gui
```

If Qt crashes before the window opens, collect environment details without importing Qt:

```bash
heirloom-gui --diagnose
```

The GUI can:

- Prompt for initial Legacy Games configuration.
- Refresh and display your game library.
- Cache cover artwork locally.
- Search and filter by install status.
- Install games.
- Launch games with recorded executables.
- Uninstall managed games.

It is a Qt 6 QML app using PySide6. It is designed to feel at home on desktop Linux and Steam Deck rather than like a quick wrapper around terminal output.

## Library Usage

Heirloom can also be imported and used from Python:

```python
from rich.pretty import pprint
from heirloom import Heirloom

h = Heirloom(
    user='YOUR_EMAIL',
    password='YOUR_PASSWORD',
    base_install_dir='~/Games/LegacyGames/',
)

user_id = h.login()
h.refresh_games_list()
pprint(h.dump_game_data('The Wild Case'))
```

Example game data:

```python
{
    'game_id': 'cc182bea-cd61-4be4-b167-3db2659c5364',
    'game_name': 'The Wild Case',
    'game_description': 'Can you survive as you investigate strange creatures with glowing eyes?',
    'game_coverart': 'https://legacygames.com/wp-content/uploads/Legacy-Games_The-Wild-Case.jpg',
    'game_installed_size': '218.1 MB',
    'installer_uuid': 'fad5198e-5c92-4493-b498-d77dc0ba6111',
    'amazonprime_giveaway': True,
}
```

## Project Status

Heirloom is usable, but it is still young. Some edges are sharp. Some installers are weird. Some Windows games are going to do Windows-game things.

The current focus is:

- Make install and uninstall behavior boringly reliable.
- Improve installed-game metadata and launch handling.
- Keep the CLI and Qt GUI backed by the same stable library behavior.
- Make the whole thing feel good on Steam Deck.

## Name

Why "Heirloom"?

Because [legendary](https://github.com/derrod/legendary) handles Epic, [nile](https://github.com/imLinguin/nile) handles Amazon, and this handles Legacy.

Legacy. Heirloom. You get it.
