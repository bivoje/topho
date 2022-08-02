
# from https://gist.github.com/aaomidi/0a3b5c9bd563c9e012518b495410dc0e
VIDEO_EXTS = set([ # play with mpv
    "webm", "mkv", "flv", "vob", "ogv", "ogg", "rrc", "gifv", "mng", "mov", "avi", "qt", "wmv", "yuv", "rm", "asf", "amv", "mp4", "m4p", "m4v", "mpg", "mp2", "mpeg", "mpe", "mpv", "m4v", "svi", "3gp", "3g2", "mxf", "roq", "nsv", "flv", "f4v", "f4p", "f4a", "f4b", "mod",

    "gif",
])

# from https://github.com/arthurvr/image-extensions/blob/master/image-extensions.json
IMAGE_EXTS = set([ # render on the window
    "ase", "art", "bmp", "blp", "cd5", "cit", "cpt", "cr2", "cut", "dds", "dib", "djvu", "egt", "exif", "gpl", "grf", "icns", "ico", "iff", "jng", "jpeg", "jpg", "jfif", "jp2", "jps", "lbm", "max", "miff", "mng", "msp", "nef", "nitf", "ota", "pbm", "pc1", "pc2", "pc3", "pcf", "pcx", "pdn", "pgm", "PI1", "PI2", "PI3", "pict", "pct", "pnm", "pns", "ppm", "psb", "psd", "pdd", "psp", "px", "pxm", "pxr", "qfx", "raw", "rle", "sct", "sgi", "rgb", "int", "bw", "tga", "tiff", "tif", "vtf", "xbm", "xcf", "xpm", "3dv", "amf", "ai", "awg", "cgm", "cdr", "cmx", "dxf", "e2d", "egt", "eps", "fs", "gbr", "odg", "svg", "stl", "vrml", "x3d", "sxd", "v2d", "vnd", "wmf", "emf", "art", "xar", "png", "webp", "jxr", "hdp", "wdp", "cur", "ecw", "iff", "lbm", "liff", "nrrd", "pam", "pcx", "pgf", "sgi", "rgb", "rgba", "bw", "int", "inta", "sid", "ras", "sun", "tga", "heic", "heif",
])

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