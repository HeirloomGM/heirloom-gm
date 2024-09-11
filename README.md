![HGM Logo](https://github.com/HeirloomGM/heirloom-gm/raw/main/docs/images/heirloom.png "Heirloom Games Manager") 

Heirloom is a library and command line tool for accessing one's game library from [Legacy Games](https://www.legacygames.com) on Linux.


### Background
---
I love my [Steam Deck](https://store.steampowered.com/steamdeck)! Most of all I love tinkering with it and seeing how many of my multitudinous games I can get to work on it.  [Heroic](https://heroicgameslauncher.com) does a great job of installing games from [Epic](https://www.epicgames.com), [GOG](https://www.gog.com), and even [Amazon Prime](https://gaming.amazon.com).  HOWEVER, sometimes Amazon's Prime Gaming giveaway game is via a not-so-well-known online game store called [Legacy Games](https://www.legacygames.com).  Heroic currently does not have an interface for Legacy Games, so I wrote this command line tool to fill that gap.  Why name it "Heirloom"?  Well, the command line utility to interface with Amazon Prime is called "[nile](https://github.com/imLinguin/nile)", and the command line utility for interfacing with Epic Games is called "[legendary](https://github.com/derrod/legendary)", so I figured Legacy -> Heirloom?


### Requirements
---
Heirloom depends on the following third-party libraries:
```
requests
typer
rich
InquirerPy
cryptography
keyring
```


### Installation
---
I always prefer to work in a virtual environment:
```bash
python3 -m venv ~/heirloom.venv
source ~/heirloom.venv/bin/activate
pip install git+https://github.com/heirloom-gm/heirloom-gm
```


### Configuration
---
The config file for the CLI is stored in JSON format and is stored by default in `~/.config/heirloom/config.json`. The password stored in the file is encrypted with a random encryption key that is generated when the CLI is first run.


### CLI Usage
---
`pip` will install a command line tool called `heirloom-gm`.

Basic commands are as follows:

Option | Description
--- | ---
list | Lists games in your Legacy Games library.
info | Prints a JSON blob representing a game from the Legacy Games API.
download | Downloads a game from the Legacy Games library and saves the installation file to the current folder.
install | Installs a game from the Legacy Games library.
uninstall | Uninstalls a game from the Legacy Games library.

Examples:

```bash
heirloom-gm list
```
```
                                           Legacy Games                                           
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Game Name                                  ┃                 UUID                 ┃ Installed? ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ House Of 1000 Doors: Family Secrets        │ db01c49e-dc08-4cf2-8dda-bc24b633691d │    Unknown │
│ The Wild Case                              │ fad5198e-5c92-4493-b498-d77dc0ba6111 │    Unknown │
│ Angelo and Deemon: One Hell of a Quest     │ 5bf49a07-2c0c-41e6-bc31-f0eb85325e56 │    Unknown │
│ Varenje                                    │ 795f44bf-ad46-41e2-9528-512048969d73 │    Unknown │
└────────────────────────────────────────────┴──────────────────────────────────────┴────────────┘
```
```bash
heirloom-gm download --game "The Wild Case"
```
```
Downloading The Wild Case (218.1 MB) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
Successfully downloaded The Wild Case setup executable as TheWildCase_N28M1FX.exe
```
```bash
heirloom-gm info
```
```
? Select a game:  The Wild Case
{
   'game_id': 'cc182bea-cd61-4be4-b167-3db2659c5364',
   'game_name': 'The Wild Case',
   'game_description': 'Can you survive as you investigate strange creatures with glowing eyes?',
   'game_coverart': 'https://legacygames.com/wp-content/uploads/Legacy-Games_The-Wild-Case.jpg',
   'game_installed_size': '218.1 MB',
   'installer_uuid': 'fad5198e-5c92-4493-b498-d77dc0ba6111',
   'amazonprime_giveaway': True
}
```


### Library usage
---
I was trying to make something that could be easily imported and used in other programs, so in addition to the CLI, you can also import the module and call its functions programmatically.

```python
from rich.pretty import pprint
from heirloom import Heirloom

h = Heirloom(user='YOUR_EMAIL', password='YOUR_PASSWORD', base_install_dir='~/Games/LegacyGames/')
user_id = h.login()
h.refresh_games_list()
pprint(h.dump_game_data("The Wild Case"))
```
```
{
   'game_id': 'cc182bea-cd61-4be4-b167-3db2659c5364',
   'game_name': 'The Wild Case',
   'game_description': 'Can you survive as you investigate strange creatures with glowing eyes?',
   'game_coverart': 'https://legacygames.com/wp-content/uploads/Legacy-Games_The-Wild-Case.jpg',
   'game_installed_size': '218.1 MB',
   'installer_uuid': 'fad5198e-5c92-4493-b498-d77dc0ba6111',
   'amazonprime_giveaway': True
}
```