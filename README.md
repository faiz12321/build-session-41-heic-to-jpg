# Fictional HEIC-to-JPEG practice, new outputs only

Python3.10+, Pillow12.0.0, pillow-heif1.8.1 and separately installed ImageMagick
with HEIC decoding. Ubuntu24.04 may require the separate
libheif-plugin-libde265 package even if HEIC is listed. This is not an iPhone-photo or library-preservation tool.
Use only trusted tiny fictional practice first. Native media decoders are not a
security sandbox. Keep originals and backups. Do not disable security policies,
codec limits or organizational restrictions to get a file to decode.

    python -m pip install Pillow==12.0.0 pillow-heif==1.8.1
    python make_sample.py
    python convert_heic.py photos jpg-practice
    python -m unittest -v

Use a NEW empty lesson folder. Setup exclusively creates three tiny fictional
HEIC-encoded colored shapes in a NEW photos folder. They are not photographs.
A repeated setup refuses rather than resetting the old folder. After interrupted
setup use a different new lesson folder; do not delete old data to force retry.

Conversion requires a NEW output folder OUTSIDE the source. It writes decoded
JPEG bytes with exclusive creation and compares all source filenames and SHA256
digests after success. Any old output path refuses, including existing directories,
files and dangling links. A failed batch can leave a partial folder. No automatic
cleanup, rollback or retry; keep originals and inspect what happened.

## What is deliberately lost or changed

Only image index0 is selected, orientation is applied, alpha is flattened onto
white, metadata/profiles/comments are stripped and JPEG quality90 is lossy.
No promise for color, dates, HDR, extra frames, Live Photo motion, depth, camera
metadata, visual equality or archival preservation. A JPEG that decodes is not
proof it preserves what matters about a real photograph.

## Executable discovery

--magick supplies an executable path/name; MAGICK_EXE can supply it too.
Default magick is searched on PATH. If absent, Windows accepts exactly one
ImageMagick*/magick.exe below Program Files; Ubuntu may use ImageMagick6's
convert name. Version output must identify ImageMagick. Multiple Windows
candidates need an explicit path. This check is not executable authentication;
use your own trusted installation. A fresh terminal can inherit stale PATH from
its parent; it is not a universal fix. Install/build/delegate/policy differences
can make conversion unavailable. Some ImageMagick builds include graphical
programs; this lesson uses its command-line conversion tool.

## Narrow input and safety contract

Nonrecursive1-100 HEICs only, simple ASCII stems of1-64letters/digits/_/-.
25MiB/file,100MiB selected total. Other entries, subfolders, case-colliding output
names, traversal spellings, filesystem links/reparse points and hardlinks are
refused. Native memory/map/disk/time limits and subprocess timeout are best-effort,
not a security or complete resource sandbox. Python buffers image bytes too.
Stop editors/sync; no hostile-race or concurrent-filesystem guarantee. File names,
paths, errors, native cache and photos can be private. No upload/network code
in setup/conversion; package installation does use the network. Other software
and cloud sync are outside its control.

## Evidence status

Two Windows and two Ubuntu full replays pass 27 small fixture tests. Windows
skips Unixpipe and case-distinct filename creation; Ubuntu runs all 27. Per-platform
pairs differ in dependency-install vs already-installed logs, unique expected
setup-refusal temp path and unittest time. Visible command portions otherwise
match. Ubuntu recorded ImageMagick6.9.12-98/libheif1.17.6 and separate
libheif-plugin-libde265. HEIC was listed before the plugin, but decoding failed;
the plugin is a real separate dependency, not a cosmetic option.

Checks cover all 3 source bytes/mtimes, all 3 JPEG decodes/dimensions/nonuniform
pixels, empty EXIF, repeat prior-output bytes/mtimes, old-file/folder preservation,
invalid source/result bytes, unsafe paths/pipe, source-change detection,
output-inside-source preflight and injected second-copy failure. Test/recorder
remove only their own unique temporary trees. Symlinks can skip if unavailable.
11 phone stages at320/390/1280 and three exact clipboard values pass, no page
overflow or JavaScript errors; actual pixels inspected. Tiny generated shapes
are not proof of real-camera color, metadata or preservation.

Source/lesson code uses MIT. Dependencies are separately installed, not bundled.
Pillow, pillow-heif/libheif, ImageMagick and codec dependencies have their own
licenses and possible patent/codec terms; this is not a legal clearance.

Sources:
- https://imagemagick.org/download/
- https://imagemagick.org/command-line-options/
- https://imagemagick.org/convert/
- https://imagemagick.org/script/formats.php
- https://imagemagick.org/security-policy/
- https://pypi.org/project/pillow-heif/
- https://pillow-heif.readthedocs.io/en/latest/saving-images.html
