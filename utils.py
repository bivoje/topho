
# from https://gist.github.com/aaomidi/0a3b5c9bd563c9e012518b495410dc0e
VIDEO_EXTS = set([ # play with mpv
    "webm", "mkv", "flv", "vob", "ogv", "ogg", "rrc", "gifv", "mng", "mov", "avi", "qt", "wmv", "yuv", "rm", "asf", "amv", "mp4", "m4p", "m4v", "mpg", "mp2", "mpeg", "mpe", "mpv", "m4v", "svi", "3gp", "3g2", "mxf", "roq", "nsv", "flv", "f4v", "f4p", "f4a", "f4b", "mod",

    "gif",
])

# from https://github.com/arthurvr/image-extensions/blob/master/image-extensions.json
IMAGE_EXTS = set([ # render on the window
    "ase", "art", "bmp", "blp", "cd5", "cit", "cpt", "cr2", "cut", "dds", "dib", "djvu", "egt", "exif", "gpl", "grf", "icns", "ico", "iff", "jng", "jpeg", "jpg", "jfif", "jp2", "jps", "lbm", "max", "miff", "mng", "msp", "nef", "nitf", "ota", "pbm", "pc1", "pc2", "pc3", "pcf", "pcx", "pdn", "pgm", "PI1", "PI2", "PI3", "pict", "pct", "pnm", "pns", "ppm", "psb", "psd", "pdd", "psp", "px", "pxm", "pxr", "qfx", "raw", "rle", "sct", "sgi", "rgb", "int", "bw", "tga", "tiff", "tif", "vtf", "xbm", "xcf", "xpm", "3dv", "amf", "ai", "awg", "cgm", "cdr", "cmx", "dxf", "e2d", "egt", "eps", "fs", "gbr", "odg", "svg", "stl", "vrml", "x3d", "sxd", "v2d", "vnd", "wmf", "emf", "art", "xar", "png", "webp", "jxr", "hdp", "wdp", "cur", "ecw", "iff", "lbm", "liff", "nrrd", "pam", "pcx", "pgf", "sgi", "rgb", "rgba", "bw", "int", "inta", "sid", "ras", "sun", "tga", "heic", "heif",
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
    # "{t    :iso}".format(t=t) == '2022-08-02T07:23:45+0900'
    # "{t.utc:iso}".format(t=t) == '2022-08-01T22:23:45+0000'
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
        return self('%Y-%m-%dT%H:%M:%S%z')

    def get_utc(self):
        return HandyTime(self.datetime.astimezone(timezone.utc))


class HandySlice:
    def __init__(self, slc, sep=''):
        self.slc = slc
        self.sep = sep

    def new(self, slc):
        return HandySlice(slc)

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
        if self.integer == 0: return ""
        ret = format_spec.split('!', 2)
        if len(ret) == 2:
            prefix, suffix = ret
            spec = ''
        elif len(ret) == 3:
            prefix, suffix, spec = ret
        else:
            prefix, suffix = '', ''
            spec = format_spec
        return prefix + super(HermitDup, self).__format__(spec) + suffix


# %%
from collections import deque
from threading import Thread, Lock, Semaphore
from PIL import ImageTk,Image

def load_tk_image(path, maxw, maxh):
    img = Image.open(str(path))
    width, height = img.size
    ratio = min(maxw/width, maxh/height)
    if ratio < 1 or 5 < ratio:
        # int cast is mandatory. otherwise, it returns None
        img = img.resize((int(width*ratio), int(height*ratio)), Image.ANTIALIAS)
    return ImageTk.PhotoImage(img)

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