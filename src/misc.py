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


import PIL.Image
import PIL.ImageTk

def load_tk_image(path, maxw, maxh):
    img = PIL.Image.open(str(path))
    width, height = img.size
    ratio = min(maxw/width, maxh/height)
    if ratio < 1 or 5 < ratio:
        # int cast is mandatory. otherwise, img.resize returns None
        img = img.resize((int(width*ratio), int(height*ratio)), PIL.Image.ANTIALIAS)
    return PIL.ImageTk.PhotoImage(img)


import json
def dump_selection(f, source_dir, selections):
    data = {
        "info": "https://github.com/bivoje/topho",
        "version": VERSION,
        "type": "selection_dump",
        "working_dir": str(Path.cwd()),
        "source_dir": str(source_dir),
        #"sort_by": ...
        "selections": [ (str(path), sel) for path, sel in selections ],
    }
    json.dump(data, f, indent=2)

def load_selection(f): return json.load(f) # TODO handle json error in case the user edited it wrongly

def dump_mapping(f, mappings):
    data = {
        "info": "https://github.com/bivoje/topho",
        "version": VERSION,
        "type": "mapping_dump",
        #"parent_dir": parent_dir,
        "mapping": [ (str(src), str(dst)) for src, dst in mappings ],
    }
    json.dump(data, f, indent=2)

def load_mapping(f): return json.load(f) # TODO handle json error in case the user edited it wrongly