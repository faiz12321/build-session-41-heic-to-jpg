"""Fictional HEIC-to-JPEG practice. New output folder only.

Python3.10+, Pillow and a separately installed ImageMagick executable.
First image only. No metadata, HDR, sequence, motion/depth or quality guarantee.
Use trusted small practice only. Stop editors/sync. Not a security sandbox.
"""
from pathlib import Path
import argparse
import hashlib
import io
import os
import re
import shutil
import stat
import subprocess
from PIL import Image


def safe_path(value, directory=False, new=False):
    path = Path(value).absolute()
    if '..' in path.parts:
        raise OSError('Parent-traversal paths are unsupported.')
    parts = [*reversed(path.parents)] + ([] if new else [path])
    for part in parts:
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise OSError('Links/reparse points are unsupported.')
    if new:
        if path.exists() or path.is_symlink():
            raise FileExistsError('Output path exists. Nothing replaced.')
    else:
        info = path.lstat()
        if directory:
            if not stat.S_ISDIR(info.st_mode):
                raise OSError('Expected an ordinary directory.')
        elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise OSError('Expected an ordinary singly linked file.')
    return path


def inventory(folder):
    folder = safe_path(folder, directory=True)
    entries = sorted(folder.iterdir(), key=lambda p: p.name)
    if not entries or len(entries) > 100:
        raise OSError('Use 1-100 HEIC files, without subfolders or other entries.')
    result = {}
    for path in entries:
        safe_path(path)
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}\.[hH][eE][iI][cC]', path.name):
            raise OSError('Only simple ASCII .heic names are supported.')
        if path.stat().st_size > 25 * 1024 * 1024:
            raise OSError('A HEIC file exceeds 25MiB.')
        data = path.read_bytes()
        if len(data) > 25 * 1024 * 1024:
            raise OSError('A HEIC file exceeds 25MiB.')
        result[path.name] = hashlib.sha256(data).hexdigest()
    if sum(p.stat().st_size for p in entries) > 100 * 1024 * 1024:
        raise OSError('Selected HEIC files exceed 100MiB.')
    stems = [p.stem.lower() for p in entries]
    if len(set(stems)) != len(stems):
        raise OSError('Case-colliding output names are unsupported.')
    return folder, result


def convert(source, destination, executable):
    source, before = inventory(source)
    destination = safe_path(destination, new=True)
    if source in destination.parents:
        raise OSError('Output must be outside the source folder.')
    # The supplied executable is a separately installed, trusted local program.
    found = shutil.which(executable)
    if not found and executable == 'magick':
        if os.name == 'nt':
            candidates = list(Path(os.environ.get('ProgramFiles','C:/Program Files')).glob('ImageMagick*/magick.exe'))
            if len(candidates) == 1:
                found = str(candidates[0])
        else:
            found = shutil.which('convert')  # ImageMagick6 name, verified below.
    if not found:
        raise OSError('ImageMagick executable not found; check the exact installed path.')
    version = subprocess.run([found, '-version'], capture_output=True, timeout=10)
    if version.returncode or b'ImageMagick' not in version.stdout:
        raise OSError('Executable did not identify itself as ImageMagick.')
    destination.mkdir()  # Existing path refuses, including a dangling link.
    for name in before:
        args = [found, '-limit', 'memory', '256MiB', '-limit', 'map', '256MiB',
                '-limit', 'disk', '256MiB', '-limit', 'time', '60',
                str(source / name) + '[0]', '-auto-orient', '-background', 'white',
                '-alpha', 'remove', '-alpha', 'off', '-strip', '-quality', '90', 'JPEG:-']
        run = subprocess.run(args, capture_output=True, timeout=70)
        if run.returncode:
            detail = run.stderr.decode('utf-8',errors='replace')[-1000:].strip()
            raise OSError('ImageMagick refused/failed; output folder may be partial. Keep originals. '+detail)
        # Decode the generated JPEG before exposing it as a completed output.
        with Image.open(io.BytesIO(run.stdout)) as image:
            if image.format != 'JPEG':
                raise OSError('Result is not a JPEG.')
            image.load()
            width, height = image.size
        output = destination / (Path(name).stem + '.jpg')
        with output.open('xb') as handle:
            handle.write(run.stdout)
        print(f'Created {output.name}: JPEG {width}x{height}')
    _, after = inventory(source)
    if after != before:
        raise OSError('Source inventory/bytes changed. Do not trust this run.')
    print(f'Checked {len(before)} source filenames and SHA256 digests unchanged.')
    print('First image only; orientation applied, alpha flattened on white, metadata stripped.')
    print('Lossy JPEG copies, not proof of color/date/HDR/Live Photo/metadata preservation.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('destination')
    parser.add_argument('--magick', default=os.environ.get('MAGICK_EXE', 'magick'))
    args = parser.parse_args()
    try:
        convert(args.source, args.destination, args.magick)
    except (OSError, ValueError, subprocess.TimeoutExpired, Image.DecompressionBombError) as exc:
        print('Stopped:', exc)
        print('No automatic cleanup/retry. Existing source/output folders are not deleted.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
