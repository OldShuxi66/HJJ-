#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_root="$repo_root/pets"
codex_home="${CODEX_HOME:-$HOME/.codex}"

pet_id="${1:-hjj}"
if [[ "$pet_id" == "--all" || "$pet_id" == "all" ]]; then
  pet_ids=()
  for pet_dir in "$source_root"/*/; do
    [[ -d "$pet_dir" ]] || continue
    pet_ids+=("${pet_dir%/}")
  done
  for i in "${!pet_ids[@]}"; do
    pet_ids[$i]="${pet_ids[$i]##*/}"
  done
  IFS=$'\n' pet_ids=($(sort <<< "${pet_ids[*]}"))
else
  pet_ids=("$pet_id")
fi

install_pet() {
  local id="$1"
  local source_dir="$source_root/$id"
  local target_dir="$codex_home/pets/$id"

  if [[ ! -d "$source_dir" ]]; then
    printf 'Unknown pet ID: %s\n' "$id" >&2
    printf 'Available IDs: ' >&2
    for pet_dir in "$source_root"/*/; do
      [[ -d "$pet_dir" ]] || continue
      printf '%s ' "${pet_dir%/}" | sed 's#^.*/##' >&2
    done
    printf '\n' >&2
    exit 1
  fi

  for name in pet.json spritesheet.webp; do
    if [[ ! -f "$source_dir/$name" ]]; then
      printf 'Required pet file not found for %s: %s\n' "$id" "$source_dir/$name" >&2
      exit 1
    fi
  done

  if [[ -f "$source_dir/pet.json" ]] && ! grep -q '"id"[[:space:]]*:[[:space:]]*"'"$id"'"' "$source_dir/pet.json"; then
    printf 'Folder and pet.json ID do not match for: %s\n' "$id" >&2
    exit 1
  fi

  local needs_backup=false
  if [[ -e "$target_dir" ]]; then
    if [[ ! -d "$target_dir" ]]; then
      printf 'The install target exists but is not a directory: %s\n' "$target_dir" >&2
      exit 1
    fi
    if [[ ! -f "$target_dir/pet.json" ]] ||
       [[ ! -f "$target_dir/spritesheet.webp" ]] ||
       ! cmp -s "$source_dir/pet.json" "$target_dir/pet.json" ||
       ! cmp -s "$source_dir/spritesheet.webp" "$target_dir/spritesheet.webp"; then
      needs_backup=true
    fi
  fi

  if [[ "$needs_backup" == true ]]; then
    local stamp
    stamp="$(date '+%Y%m%d-%H%M%S')"
    local backup_dir="$codex_home/pet-backups/$id-$stamp"
    mkdir -p "$backup_dir"
    cp -a "$target_dir" "$backup_dir/"
    printf 'Previous %s files backed up to: %s/%s\n' "$id" "$backup_dir" "$id"
  fi

  mkdir -p "$target_dir"
  cp "$source_dir/pet.json" "$target_dir/pet.json"
  cp "$source_dir/spritesheet.webp" "$target_dir/spritesheet.webp"
  printf '%s installed to: %s\n' "$id" "$target_dir"
}

for id in "${pet_ids[@]}"; do
  install_pet "$id"
done

printf 'Restart Codex or refresh the Pets settings, then select the installed pet.\n'
