#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from parser import parse
from analyzer import analyze
from database import insert_song, _connect


def extract_title(maidata_path: Path) -> str:
    """Read first lines of maidata.txt looking for &title=; fallback to folder name."""
    with open(maidata_path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if line.startswith('&title='):
                return line[7:].strip()
    return maidata_path.parent.name  # fallback to folder name


def main():
    parser_cli = argparse.ArgumentParser(description='Batch-tag maimai charts and populate db.sqlite')
    parser_cli.add_argument('--charts-dir', required=True, help='Path to folder of chart subdirectories')
    parser_cli.add_argument('--clear', action='store_true', help='Clear existing songs before ingesting')
    args = parser_cli.parse_args()

    charts_dir = Path(args.charts_dir)
    if not charts_dir.is_dir():
        print(f"Error: --charts-dir '{charts_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    covers_dir = Path(__file__).parent / 'static' / 'covers'
    covers_dir.mkdir(parents=True, exist_ok=True)

    if args.clear:
        conn = _connect()
        conn.execute("DELETE FROM songs")
        conn.commit()
        conn.close()
        print("Cleared existing songs.")

    ok_count = 0
    skip_count = 0

    for song_dir in sorted(charts_dir.iterdir()):
        if not song_dir.is_dir():
            continue

        # Skip 宴会铺面 — folder names start with [kanji]
        if song_dir.name.startswith('['):
            print(f"[SKIP] {song_dir.name} — 宴会铺面 ignored")
            skip_count += 1
            continue

        maidata = next(song_dir.rglob('maidata.txt'), None)
        if maidata is None:
            print(f"[SKIP] {song_dir.name} — no maidata.txt found")
            skip_count += 1
            continue

        try:
            features = parse(str(maidata))
            result = analyze(features)
            tags = result.get('tags', ['Balanced'])
            difficulty = result.get('difficulty')

            name = extract_title(maidata)

            bg_image_url = None
            bg_jpg = song_dir / 'bg.jpg'
            if bg_jpg.exists():
                song_id = f"{ok_count + 1:04d}"
                dest = covers_dir / f"{song_id}.jpg"
                shutil.copy2(bg_jpg, dest)
                bg_image_url = f"/static/covers/{song_id}.jpg"

            insert_song(name, tags, difficulty, None, bg_image_url)
            print(f"[OK] {name} — tags: {tags}, difficulty: {difficulty}")
            ok_count += 1

        except Exception as e:
            print(f"[SKIP] {song_dir.name} — {e}")
            skip_count += 1

    print(f"\nDone: {ok_count} songs ingested, {skip_count} skipped.")


if __name__ == '__main__':
    main()
