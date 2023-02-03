#! /usr/bin/env bash

set -x

game_dir="$HOME/.local/share/Steam/steamapps/common/Stellaris"
game_dir="${1:-$game_dir}"

sed_args=(
  # dos2unix
)

sed < "$game_dir/common/game_rules/00_rules.txt" \
  -e 's|\s*\r$||' \
  -e 's|^\(\w\+\)|patch_game_rules_\1|' \
  > ./common/scripted_triggers/00_patch_game_rules.txt

awk < "$game_dir/common/game_rules/00_rules.txt" \
  '/^\w+ = /{ printf "%s = { patch_game_rules_%s = yes }\n", $1, $1 }' \
  > ./common/game_rules/01_patch_game_rules.txt
