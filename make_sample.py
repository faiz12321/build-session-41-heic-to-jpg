"""Generate three tiny fictional HEIC pictures, exclusively in a NEW folder.
Requires separately installed Pillow and pillow-heif. Not iPhone photos.
"""
from pathlib import Path
import io
import stat
from PIL import Image, ImageDraw
import pillow_heif


def make(folder):
    folder = Path(folder).absolute()
    if '..' in folder.parts:
        raise OSError('Parent-traversal setup paths are unsupported.')
    for part in reversed(folder.parents):
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise OSError('Linked/reparse parents are unsupported.')
    folder.mkdir()
    pillow_heif.register_heif_opener()
    for i, size in enumerate([(64,48),(80,60),(48,48)],1):
        image = Image.new('RGB', size, (20*i,80,160))
        draw = ImageDraw.Draw(image)
        draw.rectangle((4,4,size[0]//2,size[1]-5), fill=(220,50*i,30))
        draw.line((0,0,size[0]-1,size[1]-1), fill='white', width=3)
        buffer = io.BytesIO()
        image.save(buffer, format='HEIF', quality=80)
        with (folder / f'sample{i}.heic').open('xb') as handle:
            handle.write(buffer.getvalue())
    print('Created three tiny fictional HEIC pictures. No real photos.')


if __name__ == '__main__':
    try:
        make(Path(__file__).absolute().parent/'photos')
    except OSError as exc:
        raise SystemExit('Stopped: '+str(exc)+'. Nothing reset or deleted.')
