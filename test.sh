#!/bin/bash

rm -rf ~/Games/LegacyGames
rm -rf ~/.config/heirloom

function sleep_timer() {
python -c """from rich.console import Console
from time import sleep
with Console().status('Sleeping :zzz:'):
    sleep(5)
"""
}

pip install . &&
echo 'Getting help...' &&
heirloom-gm --help &&
sleep_timer &&
echo 'Listing games help' &&
heirloom-gm list --help &&
sleep_timer &&
echo 'Downloading random game help' &&
heirloom-gm download --help &&
sleep_timer &&
echo 'Installing random game help' &&
heirloom-gm install --help &&
sleep_timer &&
echo 'Info from random game help' &&
heirloom-gm info --help &&
sleep_timer &&
echo 'Listing all games...' &&
heirloom-gm list &&
sleep_timer &&
echo 'Listing installed games...' &&
heirloom-gm list --installed &&
sleep_timer &&
echo 'Listing not installed games...' &&
heirloom-gm list --not-installed &&
sleep_timer &&
echo 'Downloading random game...' &&
heirloom-gm download &&
sleep_timer &&
echo 'Downloading specific game...' &&
heirloom-gm download --game "Lyne" &&
sleep_timer &&
echo 'Installing random game...' &&
heirloom-gm install &&
sleep_timer &&
echo 'Installing specific game...' &&
heirloom-gm install --game "Lyne" &&
sleep_timer &&
echo 'Getting info from random game...' &&
heirloom-gm info &&
sleep_timer &&
echo 'Getting info for specific game...' &&
heirloom-gm info --game "Lyne"

rm *.exe