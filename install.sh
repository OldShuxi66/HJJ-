#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$repo_root/pet/hjj"
codex_home="${CODEX_HOME:-$HOME/.codex}"
target_dir="$codex_home/pets/hjj"

for name in pet.json spritesheet.webp; do
  if [[ ! -f "$source_dir/$name" ]]; then
    printf 'Required pet file not found: %s\n' "$source_dir/$name" >&2
    exit 1
  fi
done

needs_backup=false
if [[ -e "$target_dir" ]]; then
  if [[ ! -d "$target_dir" ]]; then
    printf 'The HJJ install target exists but is not a directory: %s\n' "$target_dir" >&2
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
  stamp="$(date '+%Y%m%d-%H%M%S')"
  backup_dir="$codex_home/pet-backups/hjj-$stamp"
  mkdir -p "$backup_dir"
  cp -a "$target_dir" "$backup_dir/"
  printf 'Previous HJJ files backed up to: %s/hjj\n' "$backup_dir"
fi

mkdir -p "$target_dir"
cp "$source_dir/pet.json" "$target_dir/pet.json"
cp "$source_dir/spritesheet.webp" "$target_dir/spritesheet.webp"

printf 'HJJ installed to: %s\n' "$target_dir"
printf 'Restart Codex or refresh the Pets settings, then select HJJ.\n'
