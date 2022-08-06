# %%
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

# %%
# string format only allows attribute access & formatting. (no method calls!)
# so we need to wrap some formatting features via __getattr__ and __format__ methods.
# generally, __getattr__ returns the same class while __format__ returns string

# an error exists in a format string using Handy* features gets revealed at any attempt.
# in other words, once str.format runs without an error, you can rely on it.
# or you can say, all erros are statically caught.

from datetime import datetime, timezone

#class HandyTime(time.struct_time):
# cannot subclass directly since struc_time is c-struct internally
# https://stackoverflow.com/a/10114382
class HandyTime:
    # t = HandyTime(time.struct_time((2022,8,2,7,23,45,0,0,0)).astimezone())
    # "{t        }".format(t=t) == '2022-08-02'
    # "{t    :iso}".format(t=t) == '2022-08-02T07-23-45+0900'
    # "{t.utc:iso}".format(t=t) == '2022-08-01T22-23-45+0000'
    # "{t.day :03}".format(t=t) == '002'
    # "{t  :%Y_%S}".format(t=t) == '2022_45'
    def __init__(self, dt):
        assert isinstance(dt, datetime)
        self.datetime = dt

    def __getattr__(self, key):
        if key == 'utc':
            return self.get_utc()
        return self.datetime.__getattribute__(key)

    # https://docs.python.org/3/library/time.html#time.strftime
    def __call__(self, format):
        try:
            return self.datetime.strftime(format)
        except ValueError:
            raise ValueError(f"invalid formatting '{format}'")

    def __str__(self):
        return self.iso()

    # https://docs.python.org/3/reference/datamodel.html#object.__format__
    # "The format_spec argument is a string that contains a description of the
    #  formatting options desired. The interpretation of the format_spec
    #  argument is up to the type implementing __format__()"
    def __format__(self, format_spec):
        if format_spec == 'iso':
            return self.iso()
        if format_spec == '':
            return self('%Y-%m-%d')
        return self(format_spec)

    def iso(self):
        return self('%Y-%m-%dT%H-%M-%S%z')

    def get_utc(self):
        return HandyTime(self.datetime.astimezone(timezone.utc))


class HandySlice:
    def __init__(self, slc, sep=''):
        self.slc = slc
        self.sep = sep

    def new(self, slc):
        return HandySlice(slc, sep=self.sep)

    def __str__(self):
        return str(self.slc)

    def __repr__(self):
        return repr(self.slc)

    def __getattr__(self, key):
        def intp(s):
            try:
                return int(s) if s[0] != 'm' else -int(s[1:])
            except:
                raise ValueError("could not parse '{s}' as an index in {key}")

        if key[0:2] == '__':
            s, e = None, intp(key[1:])
        elif key[0] == '_':
            if '_' not in key[1:]:
                s, e = intp(key[1:]), None
            else:
                se = key[1:].split('_')
                if len(se) != 2:
                    raise ValueError(f"invalid slicing attribute format '{key}'")
                s, e = intp(se[0]), intp(se[1])
        else:
            raise ValueError(f"slicing attribute starts with '_' but found '{key}'")

        return self.new(self.slc[s:e])

    def __format__(self, format_spec):
        ret = format_spec.split('!', 1)
        if len(ret) == 2:
            sep, spec = ret
        else:
            sep, spec = self.sep, format_spec

        return sep.join(format(x, spec) for x in self.slc)


class HandyString(HandySlice):
    # "{s._1_3}---".format(s=HandyString('asdf')) == 'sd'
    # "=={s._3:#^7}---".format(s=HandyString('asdf')) == '==##asd##---'
    def __init__(self, slc):
        assert isinstance(slc, str)
        super(HandyString, self).__init__(slc)

    def new(self, string):
        return HandyString(string)

    # bypasses parent's formatting
    def __format__(self, format_spec):
        return format(self.slc, format_spec)


class HandyInt:
    # "{n.p3.x2.d5}".format(n=HandyInt(3)) == '2'
    def __init__(self, integer):
        self.integer = integer

    def new(self, integer):
        return HandyInt(integer)

    def __getattr__(self, key):
        try:
            val = int(key[1:])
        except:
            raise ValueError(f"could not parse '{key[1:]}' as an integer in {key}")

        if key[0] == 'd':
            if val == 0:
                raise ValueError(f"can't divide with zero in '{key}'")
            ret = self.integer // val
        elif key[0] == 'p' or key[0] == 't':
            ret = self.integer + val
        elif key[0] == 'm':
            ret = self.integer - val
        elif key[0] == 'x' or key[0] == 'X':
            if val == 0:
                raise ValueError(f"use constant value 0 instead '{key}'")
            ret = self.integer * val
        elif key[0] == 'r' or key[0] == 'l':
            ret = self.integer % val
        else:
            raise ValueError(f"unrecognized integer arithmetic attribute '{key[0]}'")

        return self.new(ret)

    def __str__(self):
        return str(self.integer)

    def __format__(self, format_spec):
        return format(self.integer, format_spec)


class HermitDup(HandyInt):
    def __init__(self, integer):
        super(HermitDup, self).__init__(integer)

    def new(self, integer):
        return HermitDup(integer)

    def __getattr__(self, key):
        if key[0] == 'r' or key[0] == 'l':
            raise ValueError(f"can't use modulo on dup in '{key}'")
        return super(HermitDup, self).__getattr__(key)

    def __format__(self, format_spec):
        ret = format_spec.split('!', 2)
        if len(ret) == 2:
            if self.integer == 0: return ""
            prefix, suffix = ret
            spec = ''
        elif len(ret) == 3:
            if self.integer == 0: return ""
            prefix, suffix, spec = ret
        else:
            prefix, suffix = '', ''
            spec = format_spec
        return prefix + super(HermitDup, self).__format__(spec) + suffix


# %%
from collections import deque
from threading import Thread, Lock, Semaphore
import PIL.Image
import PIL.ImageTk

def load_tk_image(path, maxw, maxh):
    img = PIL.Image.open(str(path))
    width, height = img.size
    ratio = min(maxw/width, maxh/height)
    if ratio < 1 or 5 < ratio:
        # int cast is mandatory. otherwise, it returns None
        img = img.resize((int(width*ratio), int(height*ratio)), PIL.Image.ANTIALIAS)
    return PIL.ImageTk.PhotoImage(img)

class ImageLoadingQueue:
    # public methods, run on main thread

    # waiting :: [(path, info)]
    def __init__(self, waiting, min, max, maxw, maxh, debug=False):
        self.waiting = waiting # only internal methods can mutate
        self.waiting.reverse()
        self.min = min # read only
        self.max = max # read only <- TODO can be adjusted?
        self.maxw = maxw # read only
        self.maxh = maxh # read only

        self.queue = deque() # both mutate, atomic operations
        # initially released, loader fills queue on startup
        self.task_lock = Lock() # released if something should be loaded
        self.loaded = Semaphore(value=0) # # of loaded data in the queue

        self.thread = None # only main methods can mutate
        self.stop = False # only main methods can mutate
        self.debug = debug # read only

        self.empty = not self.waiting
        self.empty_lock = Lock() # to manage atominess of `empty`

    # starts the loader
    def run(self):
        if self.thread is not None:
            print("WARNING: ImageLoadingQueue is already running")
            return
        self.thread = Thread(target=self.loader_func, name="loader")
        self.thread.start()

    def quit(self):
        if self.thread is None:
            print("WARNING: ImageLoadingQueue is already stopped")
            return
        self.stop = True
        if self.task_lock.locked(): self.task_lock.release()
        self.thread.join()
        self.thread = None

    def is_empty(self):
        return self.empty

    def flush(self):
        assert not self.thread
        self.waiting.reverse()
        ret = list((a,b) for _,a,b in self.queue) + self.waiting
        self.waiting = []
        self.queue = deque()
        return ret

    # main <- queue; managed manually
    # returns `None` if empty, `False` if waiting, element if available
    def get(self, block=False, pop=True):
        self.print(f"get {block} {pop}")
        if self.is_empty(): return None

        acquired = self.loaded.acquire(blocking=block) # decrease
        if not acquired: return False

        # queue is not empty, should never throw an exception
        elem = self.queue.popleft()

        if not pop: # only peeking the data if pop=True
            self.queue.appendleft(elem)
            self.loaded.release() # increase
        else: # elem actually popped from the queue
            if self.task_lock.locked():
                # activate loader for possible loading if not already running
                self.task_lock.release()
        return elem

    # main -> queue; managed manually
    def put(self, elem):
        self.print(f"put {elem}")
        self.queue.appendleft(elem)
        self.loaded.release() # increase

        self.empty_lock.acquire()
        self.empty = False
        self.empty_lock.release()

        # activate loader for possible garbage collection
        self.task_lock.release()


    # internal methods, run on separate thread

    def loader_func(self):
        self.print("loader_func")
        while not self.stop:
            self.task_lock.acquire()
            self.print("task start!")
            # we could acquire the lock, there are jobs to be done for front queue
            while len(self.queue) < self.min and not self.stop:
                self.empty_lock.acquire()
                loaded = self.load_one()
                if not loaded:
                    self.print("no more")
                    if len(self.queue) == 0:
                        self.empty = True
                    self.empty_lock.release()
                    break # no more data to load
                else: self.empty = False # this is defensive coding. not actually needed
                self.empty_lock.release()

            while len(self.queue) > self.max and not self.stop:
                self.free_one()

            self.print("task done")
            # job done, now going to the loop start & sleep until new job is needed

    # queue <- waiting; managed automatically
    def load_one(self):
        if not self.waiting: return False
        self.print(f"load_one {len(self.queue)}")

        # from time import sleep
        # sleep(5)

        path, info = self.waiting.pop()
        if path.suffix[1:] in IMAGE_EXTS:
            try: # ensures `path` never get lost
                img = load_tk_image(path, self.maxw, self.maxh)
            except:
                img = False
        elif path.suffix[1:] in VIDEO_EXTS:
            img = 'video'
        else: # unrecognized
            img = None

        self.queue.append((img, path, info))
        self.loaded.release() # increase
        return True

    # queue -> waiting; qmanaged automatically
    def free_one(self):
        self.print(f"free_one")
        try:
            _, path, info = self.queue.pop()
            self.loaded.acquire() # decrease
            self.waiting.append((path, info))
        except IndexError:
            # when self.queue is empty. using exception for thread safety.
            return False
        return True

    def print(self, *args, **kargs):
        if self.debug: print(*args, **kargs)

# %%
from pathlib import Path
import tempfile
import os

def leave_crumbs(root, prefix='crumb'):
    #if not root.exists(): return
    for subdir in root.glob('**/'):
        fd, tpath = tempfile.mkstemp(dir=subdir, prefix=prefix)
        os.close(fd)

def collect_crumbs(root, prefix='crumb'):
    for subpath in root.glob(f'**/{prefix}*'):
        subpath.unlink()

def mimic_tree(source_root, target_root):
    for subdir in source_root.glob('**/'):
        tubdir = target_root / subdir.relative_to(source_root)
        tubdir.mkdir(parents=True, exist_ok=True)

def try_rmdir_rec(root):
    for subdir in filter(lambda p: p.is_dir(), root.iterdir()):
        if not subdir.is_dir(): continue
        try_rmdir_rec(subdir)
    try: root.rmdir()
    except OSError: pass

# %%

# source_dir must be prefix of path. (both Path object)
# returns target path object
format_name_lookup_cache = {}
def format_name(formstr, index, path, source_dir, target_dir, exists=lambda p: p.exists()):
    global format_name_lookup_cache
    assert target_dir.exists() and target_dir.is_dir()
    if path.exists():
        size = HandyInt(os.path.getsize(path)),
        # note that windows' file explorer's 'date' has more complex method of determination
        # if photo has no taken-time info, it usually is modified date (not created)
        # mod date is kept unchanged when copying & moving (to other drive)
        # https://superuser.com/a/1674290
        created  = HandyTime(datetime.fromtimestamp(os.path.getctime(path)).astimezone())
        modified = HandyTime(datetime.fromtimestamp(os.path.getmtime(path)).astimezone())
        accessed = HandyTime(datetime.fromtimestamp(os.path.getatime(path)).astimezone())
    else:
        size = HandyInt(2**(6+index*4)),
        created  = HandyTime(datetime.fromtimestamp(0,tz=timezone.utc).astimezone())
        modified = HandyTime(datetime(2013,6,5,21,54,57).astimezone())
        accessed = HandyTime(datetime(2054,6,8,4,13,26).astimezone())

    # [:-1] to removing last '.'
    parents = list(p.name for p in path.relative_to(source_dir.parent).parents)
    hier = list(reversed(parents[:-1])) + ['']

    gen = lambda dup: target_dir / (formstr.format(
        index = HandyInt(index),
        name = HandyString(path.stem),
        hier = HandySlice(hier, '\\'),
        size = size,
        created  = created,
        modified = modified,
        accessed = accessed,
        dup = HermitDup(dup),
    ) + path.suffix)

    newpath0 = gen(0)

    if not exists(newpath0): # ret0 is ok to use
        format_name_lookup_cache[str(newpath0)] = 1
        return newpath0, 0

    if newpath0 == gen(1): # considering 'dup' is not used in formatstr.
        # just return it (probably filename duplication error occures)
        return newpath0, 1

    # use 1 as default as there already is one file with the name.
    j = format_name_lookup_cache.get(str(newpath0), 1)

    while True: # FIXME this goes indefinitely.. should I add cap as an option??
        newpath = gen(j)
        if not exists(newpath):
            format_name_lookup_cache[str(newpath0)] = j+1
            return newpath, j
        j += 1


# %%
def write_remainings(f, args, source_dir, remaining, START_TIME):
    f.write(f"#Topho {VERSION}\n")
    f.write(f"#WD {Path.cwd()}\n")
    f.write(f"#SRC {source_dir}\n")
    f.write(f"#DST {args.target_dir}\n")
    f.write(f"#FMT {args.name_format}\n")
    f.write(f"#OPT {START_TIME:iso} {'copy' if args.keep else 'move'}\n")
    f.write(f"#REASON\tINDEX\tDUP\tSOURCE\tDECISION\tNOTE\n")
    for reason, idx, dup, path, dir, note in remaining:
        f.write(f"{reason}\t{idx}\t{dup}\t{path}\t{dir}\t{note}\n")

class DummyArgs:
    def __init__(self,
        source, target_dir,
        dry, keep, name_format, logfile,
        filesystem_latency,

        maxw = None, maxh = None,
        test_names = None,
        mpv = None, arx = None,
        frontq_min = None, frontq_max = None,
        backq_min = None, backq_max = None, 
    ):
        self.source = source
        self.target_dir = target_dir

        self.dry = dry
        self.keep = keep
        self.copy = keep
        self.name_format = name_format
        self.logfile = logfile
        self.filesystem_latency = filesystem_latency

        self.maxw, self.maxh = maxw, maxh
        self.test_names = test_names
        self.mpv, self.arx = mpv, arx
        self.frontq_min, self.frontq_max = frontq_min, frontq_max
        self.backq_min, self.backq_max = backq_min, backq_max

def load_remainings(f):
    ver = f.readline().rstrip('\n').split(' ', 1)[1]
    cwd = f.readline().rstrip('\n').split(' ', 1)[1]
    src = f.readline().rstrip('\n').split(' ', 1)[1]
    dst = f.readline().rstrip('\n').split(' ', 1)[1]
    fmt = f.readline().rstrip('\n').split(' ', 1)[1]
    _, time, mode = f.readline().split()
    heading = f.readline()

    args = DummyArgs(
        source = Path(src), target_dir = Path(dst),
        dry = None,
        keep = mode=='copy', name_format = fmt,
        logfile = None,
        filesystem_latency = None,
    )

    remaining = []
    #for reason, idx, dup, path, dir, note in f:
    for line in f:
        reason, idx, dup, path, dir, note = line.rstrip('\n').split('\t')
        dir = None if dir == '-' else int(dir)
        dup = None if dup == '-' else int(dup)
        remaining.append((reason, int(idx), dup, Path(path), dir, note))

    return remaining, Path(cwd), args


# %%
import shutil
from time import sleep
import sys

def organize(result, args, source_dir, temp_dir, ignored_files, START_TIME):
    target_dir_created_root = args.target_dir
    while target_dir_created_root != Path('.') and not target_dir_created_root.parent.exists():
        target_dir_created_root = target_dir_created_root.parent

    leave_crumbs(args.target_dir)
    args.target_dir.mkdir(parents=True, exist_ok=True)

    dst_dirs = [] # :: [ (path, created_by_program?) ]

    for i in range(10):
        dirpath = args.target_dir / str(i)
        if dirpath.exists():
            while dirpath.exists() and not dirpath.is_dir():
                dirpath = args.target_dir / (dirpath.name + "_")
        if not dirpath.exists():
            dirpath.mkdir()
            dst_dirs.append((dirpath,True))
        else:
            dst_dirs.append((dirpath,False))

    # files couldn't be moved
    remaining = [] # :: [(reason, idx, dup, path, dir, note)]
    skipped = []

    # FIXME i keeps increasing for skippedd, trashcaned, remaining files
    for i, (cur, dir) in result:
        if not cur.exists():
            remaining.append(('MISSING', i, '-', cur, dir, ''))
            continue

        if dir is None: # skipped files
            skipped.append(dir)
            continue

        try:
            if dir == 0: # this is a trashcan
                dst, j = format_name("{modified}[-[{hier:]-]!}{name}_{dup}", i, cur, source_dir, dst_dirs[0][0])
            else:
                dst, j = format_name(args.name_format, i, cur, source_dir, dst_dirs[dir][0])
        except Exception as e:
            # this is unlikely to happen, but if it does, make sure other files get moved safely
            print(f"while moving '{cur}' to '{dst_dirs[dir][0]}', ")
            print(e)
            print("please report this to the developer!")
            remaining.append(('FORMAT', i, '-', cur, dir, repr(e)))
            continue

        if dst.exists():
            remaining.append(('DUP', i, j, cur, dir, ''))
            continue

        if args.dry:
            print(("copying " if args.keep else "moving ") + str(cur) + " to " + str(dst) + "!")
            continue

        try:
            if args.keep:
                if not dst.parent.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    sleep(args.filesystem_latency) # wait for filesystem update
                shutil.copy2(cur, dst)
            else:
                cur.replace(dst)
                # FIXME if target subdir not exist?

        except OSError as e:
            remaining.append(('OS', i, j, cur, dir, repr(e)))

    if remaining:
        print(f"{len(remaining)} / {len(result)} files could not be {'copied' if args.keep else 'moved'}, detailed reasons are recorded.")
        if args.logfile == '-':
            write_remainings(sys.stdout, args, source_dir, remaining, START_TIME)
        else:
            try:
                with open(args.logfile, "at") as f:
                    write_remainings(f, args, source_dir, remaining, START_TIME)
            except:
                print(f"couldn't open the logfile '{args.logfile}'")
                write_remainings(sys.stdout, args, source_dir, remaining, START_TIME)
    else:
        print(f"All {len(result)} files have been {'copied' if args.keep else 'moved'} properly.")

    # remove and restore dst_dir if possible
    try_rmdir_rec(args.target_dir)
    collect_crumbs(args.target_dir)

    # remove created target_dir parents if possible
    target_dir = args.target_dir
    while target_dir_created_root != target_dir:
        try: target_dir.rmdir()
        except OSError: break
        target_dir = target_dir.parent

    try: target_dir.rmdir()
    except OSError: pass

    # try removing source_dir if possible
    # FIXME does not work if sub directory exists despite empty
    # try: source_dir.rmdir()
    # except OSError: pass

    # remove un-archived files and possibly source
    if temp_dir is not None:
        if skipped or remaining or ignored_files:
            print(f"{len(skipped) + len(remaining) + len(ignored_files)} files are still in temp dir, keeping {source_dir}")
        else:
            shutil.rmtree(temp_dir)
            pass

        if not args.keep:
            args.source[1].unlink()

    else:
        if not args.keep:
            try_rmdir_rec(source_dir)

# %%
from tkinter import *
import subprocess

class OrganHelperView:
    def __init__(self, maxw, maxh, mpvcmd, STATIC):
        self.maxw = maxw
        self.maxh = maxh
        self.mpvcmd = mpvcmd

        self.root = Tk()
        self.root.title(f"Topho {VERSION}")

        # FIXME for some reason, can't load image from main thread... :/
        # default_img = front_queue()[0]
        self.unrecog_img = load_tk_image(STATIC/'unrecognized.png', self.maxw, self.maxh)
        self.loading_img = load_tk_image(STATIC/'loading.png',      self.maxw, self.maxh)
        self.broken_img  = load_tk_image(STATIC/'broken.png',       self.maxw, self.maxh)
        self.video_img   = load_tk_image(STATIC/'video.png',        self.maxw, self.maxh)
        self.start_img   = load_tk_image(STATIC/'start.png',        self.maxw, self.maxh)
        self.end_img     = load_tk_image(STATIC/'end.png',          self.maxw, self.maxh)
        self.lab = Label(image=self.start_img)
        self.lab.grid(row=0,column=1,columnspan=3)

        self.last_key = None
        self.key_released = True
        self.started = False
        self.commit = False

    def load(self, supported_files, qparam):
        self.fqm, self.fqM, self.bqm, self.bqM = qparam
        self.front_queue = ImageLoadingQueue(supported_files, self.fqm, self.fqM, self.maxw, self.maxh)
        self.back_queue  = ImageLoadingQueue([],              self.bqm, self.bqM, self.maxw, self.maxh)

    def show_current(self):
        if not self.started:
            img = self.start_img
            title = f"Topho {VERSION}"
        else:
            ret = self.front_queue.get(block=False, pop=False)
            if ret is None: # no more data
                img = self.end_img
                title = "END"
            elif not ret: # loading
                img = self.loading_img
                title = "LOADING"
            else:
                img = ret[0]
                title = ('-' if ret[2] is None else str(ret[2])) + " " + ret[1].name

        if img is None: # unrecognized type
            img = self.unrecog_img
        elif not img: # image broken..
            img = self.broken_img
        elif img == 'video':
            img = self.video_img
            subprocess.Popen([self.mpvcmd, "--loop=inf", ret[1]])

        self.lab.config(image=img)
        self.lab.grid(row=0,column=1,columnspan=3)
        self.root.title(title)


    def key_press(self, e):
        if e.char == self.last_key and not self.key_released: return
        self.last_key, self.key_released = e.char, False

        if self.last_key == '\x1b':
            #print("quit")
            self.root.destroy()
            return

        if self.last_key == 'c':
            #print("commit")
            self.commit = True
            self.root.destroy()
            return

        if self.last_key == ' ' and not self.started:
            #print("start")
            self.started = True
            self.show_current()
            return

        if not self.started: return

        elif self.last_key == 'r':
            #print("reload")
            self.show_current()

        elif '0' <= self.last_key and self.last_key <= '9':
            #print("do")
            ret = self.front_queue.get(block=False)
            if ret: # no more data, do nothing
                img, orig_path, _ = ret
                self.back_queue.put((img, orig_path, int(self.last_key)))
            self.show_current()

        elif self.last_key == 'u':
            #print("undo")
            ret = self.back_queue.get()
            if ret is None: # at the start
                self.started = False
                self.show_current()
            elif not ret: # loading
                # FIXME
                self.lab.config(image=self.loading_img)
                self.lab.grid(row=0,column=1,columnspan=3)
            else:
                self.front_queue.put(ret)
                self.show_current()

        elif self.last_key == 'U':
            #print("redo")
            ret = self.front_queue.get(block=False)
            if ret: # no more data, do nothing
                self.back_queue.put(ret)
            self.show_current()

        elif self.last_key == ' ':
            #print("skip")
            ret = self.front_queue.get(block=False)
            if ret: # no more data, do nothing
                img, orig_path, _ = ret
                self.back_queue.put((img, orig_path, None))
            self.show_current()


    def key_release(self, e):
        self.key_released = True


    def run(self):
        self.front_queue.run()
        self.back_queue.run()


        self.root.bind('<KeyPress>', self.key_press)
        self.root.bind('<KeyRelease>', self.key_release)

        self.root.mainloop()

        self.front_queue.quit()
        self.back_queue.quit()

        result = self.back_queue.flush()
        result.reverse()

        return result
