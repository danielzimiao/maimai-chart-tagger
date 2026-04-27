#!/usr/bin/env python3
import argparse
import io
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import sys
from PIL import Image
from tqdm import tqdm
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from parser import parse
from analyzer import rule_analyze
from database import insert_song, _connect


def extract_title(maidata_path: Path) -> str:
    with open(maidata_path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if line.startswith('&title='):
                return line[7:].strip()
    return maidata_path.parent.name


def iter_song_dirs(charts_dir: Path):
    """Generator — yields one song dir at a time, no bulk list in memory."""
    for entry in sorted(charts_dir.iterdir()):
        if not entry.is_dir():
            continue
        if (entry / 'maidata.txt').exists():
            yield entry
        else:
            for sub in sorted(entry.iterdir()):
                if sub.is_dir() and (sub / 'maidata.txt').exists():
                    yield sub


def _process_song(song_dir: Path) -> dict:
    """Worker (runs in subprocess): parse + tag one song, return result dict.

    No DB writes, no file writes — only returns data to the main process.
    """
    if song_dir.name.startswith('['):
        return {'skip': True, 'reason': '宴会铺面'}

    maidata = song_dir / 'maidata.txt'
    try:
        features = parse(str(maidata))
        result = rule_analyze(features)
        name = extract_title(maidata)

        cover_bytes = None
        bg_src = next(
            (song_dir / f for f in ('bg.jpg', 'bg.png', 'BG.jpg', 'BG.png')
             if (song_dir / f).exists()),
            None,
        )
        if bg_src is not None:
            try:
                buf = io.BytesIO()
                with Image.open(bg_src) as im:
                    im = im.convert("RGB")
                    im.thumbnail((256, 256), Image.LANCZOS)
                    im.save(buf, "JPEG", quality=75, optimize=True)
                cover_bytes = buf.getvalue()
            except Exception:
                cover_bytes = bg_src.read_bytes()

        return {
            'name': name,
            'tags': result.get('tags', ['Balanced']),
            'difficulty': result.get('difficulty'),
            'cover_bytes': cover_bytes,
        }
    except Exception as e:
        return {'skip': True, 'reason': str(e), 'name': song_dir.name}


def main():
    parser_cli = argparse.ArgumentParser(description='Batch-tag maimai charts and populate db.sqlite')
    parser_cli.add_argument('--charts-dir', required=True)
    parser_cli.add_argument('--clear', action='store_true')
    parser_cli.add_argument('--workers', type=int, default=os.cpu_count(),
                            help='Parallel workers (default: cpu count)')
    args = parser_cli.parse_args()

    charts_dir = Path(args.charts_dir)
    if not charts_dir.is_dir():
        print(f"Error: '{charts_dir}' is not a directory.", file=sys.stderr)
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

    # Count total without loading content (just paths)
    total = sum(1 for _ in iter_song_dirs(charts_dir))
    print(f"Found {total} song dirs, using {args.workers} workers.")

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(_process_song, d): d for d in iter_song_dirs(charts_dir)}

        with tqdm(as_completed(futures), total=total, unit="song", ncols=90) as bar:
            for future in bar:
                song_dir = futures[future]
                try:
                    result = future.result()
                except Exception as e:
                    tqdm.write(f"[ERR] {song_dir.name} — {e}")
                    skip_count += 1
                    bar.set_postfix(ok=ok_count, skip=skip_count)
                    continue

                if result.get('skip'):
                    skip_count += 1
                    bar.set_postfix(ok=ok_count, skip=skip_count)
                    continue

                # Write cover (main process only — no concurrency issue)
                bg_image_url = None
                if result['cover_bytes']:
                    song_id = f"{ok_count + 1:04d}"
                    dest = covers_dir / f"{song_id}.jpg"
                    dest.write_bytes(result['cover_bytes'])
                    bg_image_url = f"/static/covers/{song_id}.jpg"

                insert_song(result['name'], result['tags'], result['difficulty'],
                            None, bg_image_url)
                ok_count += 1
                bar.set_postfix(ok=ok_count, skip=skip_count,
                                song=result['name'][:18])

    print(f"\nDone: {ok_count} ingested, {skip_count} skipped.")


if __name__ == '__main__':
    main()
