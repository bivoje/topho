VERSION = "2.0.0"

# from https://gist.github.com/aaomidi/0a3b5c9bd563c9e012518b495410dc0e
VIDEO_EXTS = set([ # play with mpv
    "webm", "mkv", "flv", "vob", "ogv", "ogg", "rrc", "gifv", "mng", "mov", "avi", "qt", "wmv", "yuv", "rm", "asf", "amv", "mp4", "m4p", "m4v", "mpg", "mp2", "mpeg", "mpe", "mpv", "m4v", "svi", "3gp", "3g2", "mxf", "roq", "nsv", "flv", "f4v", "f4p", "f4a", "f4b", "mod",

    "gif",
])

# from https://github.com/arthurvr/image-extensions/blob/master/image-extensions.json
IMAGE_EXTS = set([ # render on the window
    "ase", "art", "bmp", "blp", "cd5", "cit", "cpt", "cr2", "cut", "dds", "dib", "djvu", "egt", "exif", "gpl", "grf", "icns", "ico", "iff", "jng", "jpeg", "jpg", "jfif", "jp2", "jps", "lbm", "max", "miff", "mng", "msp", "nef", "nitf", "ota", "pbm", "pc1", "pc2", "pc3", "pcf", "pcx", "pdn", "pgm", "PI1", "PI2", "PI3", "pict", "pct", "pnm", "pns", "ppm", "psb", "psd", "pdd", "psp", "px", "pxm", "pxr", "qfx", "raw", "rle", "sct", "sgi", "rgb", "int", "bw", "tga", "tiff", "tif", "vtf", "xbm", "xcf", "xpm", "3dv", "amf", "ai", "awg", "cgm", "cdr", "cmx", "dxf", "e2d", "egt", "eps", "fs", "gbr", "odg", "svg", "stl", "vrml", "x3d", "sxd", "v2d", "vnd", "wmf", "emf", "art", "xar", "png", "webp", "jxr", "hdp", "wdp", "cur", "ecw", "iff", "lbm", "liff", "nrrd", "pam", "pcx", "pgf", "sgi", "rgb", "rgba", "bw", "int", "inta", "sid", "ras", "sun", "tga", "heic", "heif",
])

# from https://github.com/sindresorhus/archive-extensions/blob/main/archive-extensions.json
ARXIV_EXTS = set([
	"7z", "a", "ace", "apk", "ar", "arc", "bz2", "cab", "chm", "cpio", "deb", "dmg", "ear", "egg", "epub", "gz", "iso", "jar", "lz", "lzma", "lzo", "mar", "pea", "pet", "pkg", "rar", "rpm", "s7z", "sit", "sitx", "shar", "tar", "tbz2", "tgz", "tlz", "txz", "war", "whl", "xpi", "xz", "zip", "zipx", "zst",

    "egg",
])

class TophoError(Exception):
    pass

from pathlib import Path
SCRIPTDIR = Path(__file__).parent

DEBUG = True

def debug(*args, **kargs):
    if DEBUG: print("topho_debug:", *args, **kargs)

def check_dirname(dirname):
    return not any(c in dirname for c in '/\\:*?"<>|')

import PIL.Image
import PIL.ImageTk

def load_tk_image(path, maxw, maxh):
    img = PIL.Image.open(str(path))
    width, height = img.size
    ratio:int = min(maxw/width, maxh/height)
    if ratio < 1 or 5 < ratio:
        # int cast is mandatory. otherwise, img.resize returns None
        img = img.resize((int(width*ratio), int(height*ratio)), PIL.Image.ANTIALIAS) # type: ignore
    return PIL.ImageTk.PhotoImage(img)


import json
def dump_selection(f, source_dir, ignored, dirnames, selections):
    encode = json.JSONEncoder().encode
    ignored = list(ignored)

    # using custom json encoding; faster, neater
    f.write('{\n')
    f.write(f'  "info": "https://github.com/bivoje/topho",\n')
    f.write(f'  "version": "{VERSION}",\n')
    f.write(f'  "type": "selection_dump",\n')
    f.write(f'  "working_dir": {encode(str(Path.cwd()))},\n')
    f.write(f'  "source_dir": {encode(str(source_dir))},\n')
    #TODO f.write(f'  "sort_by": ...,\n')

    if any(dirnames):
        f.write(f'  "dirnames": [\n') # FYI field
        for i, path in enumerate(dirnames):
            if i > 0: f.write(',\n')
            f.write(f'    {encode(str(path))}')
        f.write(f'\n  ],\n')

    f.write(f'  "ignored_files": [\n') # FYI field
    for i, path in enumerate(ignored):
        if i > 0: f.write(',\n')
        f.write(f'    {encode(str(path))}')
    f.write(f'\n  ],\n')

    sel_count = [0] * 11 # sel_count[10] = sel_count[-1] = skipped
    f.write(f'  "selections": [\n')
    for i, (path, sel) in enumerate(selections):
        if i > 0: f.write(',\n')
        f.write(f'    [ {sel if sel is not None else "null"},\t{encode(str(path))} ]')
        if sel is not None:
            sel_count[sel] += 1
        else:
            sel_count[-1] += 1
    f.write(f'\n  ],\n')

    f.write(f'  "num_ignored": {len(ignored)},\n') # FYI field
    f.write(f'  "num_selection": {len(selections)-sel_count[-1]},\n') # FYI field
    f.write(f'  "num_skipped": {sel_count[-1]},\n') # FYI field
    f.write(f'  "num_each": [ {", ".join(map(str,sel_count[:-1]))} ]\n') # FYI field

    f.write('}\n')

def load_selection(f):
    try:
        dump = json.load(f)
    except json.decoder.JSONDecodeError as e:
        raise TophoError(f'JSON error in selections file: {e}')

    for x in ['version', 'type', 'source_dir', "selections", ]:
        if x not in dump:
            raise TophoError(f"'{x}' not specified in selections dump")

    data = {}

    if dump['version'] != VERSION:
        raise TophoError(f"version mismatch ({dump['version']}); should be {VERSION}")

    if dump['type'] != 'selection_dump':
        raise TophoError(f"Wrong 'type' ({dump['type']}) for selections dump")

    try:
        data['source_dir'] = Path(dump['source_dir'])
    except:
        raise TophoError(f"Malformed 'source_dir' ({dump['source_dir']}) in selections dump")

    data['dirnames'] = ['<TRASH>'] + [''] * 9
    if 'dirnames' in dump:
        if not isinstance(dump['dirnames'], list):
            raise TophoError("'dirnames' is not iterable in selections dump")

        for i, dirname in enumerate(dump['dirnames']):
            if (i == 0 and dirname != "<TRASH>") or (i != 0 and not check_dirname(dirname)):
                raise TophoError(f"Malformed in {i}'th dirname ({dirname}) in selections dump")
            data['dirnames'][i] = dirname

    if not isinstance(dump['selections'], list):
        raise TophoError("'selections' is not iterable in selections dump")
    data['selections'] = []

    for i, row in enumerate(dump['selections']):
        try:
            (sel, path) = row
            data['selections'].append((Path(path), None if sel is None else int(sel)))
        except:
            raise TophoError(f"Malformed in {i}'th selection ({row}) in selections dump")

    return data


def dump_mapping(f, skipped, mappings, source_dir, target_dir):
    encode = json.JSONEncoder().encode

    # using custom json encoding; faster, neater
    f.write('{\n')
    f.write(f'  "info": "https://github.com/bivoje/topho",\n')
    f.write(f'  "version": "{VERSION}",\n')
    f.write(f'  "type": "mapping_dump",\n')
    f.write(f'  "source_dir": {encode(str(source_dir))},\n')
    f.write(f'  "target_dir": {encode(str(target_dir))},\n')
    f.write(f'  "num_skipped": {len(skipped)},\n') # FYI field

    f.write(f'  "skipped": [\n') # FYI field
    for i, src in enumerate(skipped):
        if i > 0: f.write(',\n')
        f.write(f'    {encode(str(src))}')
    f.write(f'\n  ],\n')

    f.write(f'  "mapping": [\n')
    for i, (src, dst) in enumerate(mappings):
        if i > 0: f.write(',\n')
        f.write(f'    [ {encode(str(src))},\t{encode(str(dst))} ]')
    f.write(f'\n  ]\n')

    f.write('}\n')

def load_mapping(f):
    try:
        dump = json.load(f)
    except json.decoder.JSONDecodeError as e:
        raise TophoError(f'JSON error in selections file: {e}')

    for x in ['version', 'type', 'mapping', 'source_dir', 'target_dir']:
        if x not in dump:
            raise TophoError(f"'{x}' not specified in mapping dump")

    data = {}

    if dump['version'] != VERSION:
        raise TophoError(f"version mismatch ({dump['version']}); should be {VERSION}")

    if dump['type'] != 'mapping_dump':
        raise TophoError(f"Wrong 'type' ({dump['type']}) for mapping dump")

    try:
        data['source_dir'] = Path(dump['source_dir'])
    except:
        raise TophoError(f"Malformed 'source_dir' ({dump['source_dir']}) in mapping dump")

    try:
        data['target_dir'] = Path(dump['target_dir'])
    except:
        raise TophoError(f"Malformed 'target_dir' ({dump['target_dir']}) in mapping dump")

    if not isinstance(dump['mapping'], list):
        raise TophoError("'mapping' is not iterable in mapping dump")
    data['mapping'] = []

    for i, row in enumerate(dump['mapping']):
        try:
            (src, dst) = row
            data['mapping'].append((Path(src), None if dst is None else Path(dst)))
        except:
            raise TophoError(f"Malformed in {i}'th selection ({row}) in mapping dump")

    return data


def dump_remain(f, source_dir, target_dir, remaining):
    encode = json.JSONEncoder().encode

    f.write('{\n')
    f.write(f'  "info": "https://github.com/bivoje/topho",\n')
    f.write(f'  "version": "{VERSION}",\n')
    f.write(f'  "type": "remain_dump",\n')
    f.write(f'  "source_dir": {encode(str(source_dir))},\n')
    f.write(f'  "target_dir": {encode(str(target_dir))},\n')

    f.write(f'  "remain": [\n')
    for i, (reason, src, dst, note) in enumerate(remaining):
        if i > 0: f.write(',\n')
        f.write(f'    [ "{reason}",\t{encode(str(src))},\t{encode(str(dst))},\t"{note}" ]')
    f.write(f'\n  ]\n')
    f.write('}\n')


from handy_format import HandyTime
from datetime import datetime
import subprocess
import shutil
import os

from datetime import timedelta

def get_cachedir(arxfile, arx, START_TIME):
    time = HandyTime(datetime.fromtimestamp(os.path.getmtime(arxfile)).astimezone())
    name = arxfile.stem[:100]

    for cachedir in arxfile.parent.glob(f"tempho_*_{name}"):
        debug(f"visiting cached dir {cachedir}")

        infofile = cachedir / "tempho_info.json"
        if not infofile.exists() or infofile.is_dir() or not os.access(infofile, os.R_OK): continue
        with open(infofile, "r") as f:
            info = json.load(f)

        if info['file_path'] != str(arxfile): continue
        filetime = datetime.strptime(info['file_time'], "%Y-%m-%dT%H-%M-%S%z")
        debug(f"cachedir timediff {time:iso} - {filetime}")

        if abs((time.datetime-filetime).total_seconds()) > 1: # outdated cache
            shutil.rmtree(cachedir) # FIXME what if other file is mapping file is still using this directory??
            continue

        debug(f"using cached dir {cachedir}")
        return cachedir # found

    # no previous cache found, create new one
    cachedir = arxfile.parent / f"tempho_{START_TIME:%Y%m%d-%H%M%S}_{name}"
    command = [str(arx), 'x', '-target:auto', '-y', '-o:'+str(cachedir), str(arxfile)]
    arx_proc = subprocess.Popen(command)
    if 0 != arx_proc.wait(): raise TophoError(f"Unarchive command failed: {command}")
    # TODO can we gain time here??

    infofile = cachedir / "tempho_info.json"
    if infofile.exists(): raise TophoError(f"Cannot create infofile: {infofile}")

    with open(infofile, "w") as f:
        data = {
            'file_path': str(arxfile),
            'file_time': f"{time:iso}",
            'cache_date': f"{START_TIME:iso}",
        }
        json.dump(data, f, indent=2) # FIXME what if fail

    debug(f"created cache dir {cachedir}")
    return cachedir