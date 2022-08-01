# usage: python TOPHO\INSTALL\DIR SOURCE\DIR
# then images in SOURCE\DIR will be organized in PWD\0~9

# press SPACE to start || re-do
# press q to stop and move file
# press 0 ~ 9 to move files to the directory
# press u to un-do
# press r to reload (needed to view loading image)

# %%

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
import sys

if len(sys.argv) != 2:
    print("need source directory")
    sys.exit()

# %%
from pathlib import Path

SCRIPTDIR = Path(__file__).parent
target_dir = Path.cwd()
orig_dir = Path(sys.argv[1])

if not orig_dir.exists():
    print("source dir not exists!")
    sys.exit()

files = list((path,0) for path in orig_dir.iterdir() if not path.is_dir())

version = "1.0.0"

# %%
from tkinter import *
from PIL import ImageTk,Image

root = Tk()
root.title(f"Topho {version}")

# FIXME for some reason, can't load image from main thread... :/
# default_img = front_queue()[0]
blank_img   = ImageTk.PhotoImage(Image.new('RGB', (500, 500)))
unrecog_img = ImageTk.PhotoImage(Image.open(str(SCRIPTDIR/'unrecognized.jpg')))
loading_img = ImageTk.PhotoImage(Image.open(str(SCRIPTDIR/'loading.jpg')))
broken_img  = ImageTk.PhotoImage(Image.open(str(SCRIPTDIR/'broken.png')))
video_img   = ImageTk.PhotoImage(Image.open(str(SCRIPTDIR/'video.png')))
start_img   = ImageTk.PhotoImage(Image.open(str(SCRIPTDIR/'start.png')))
end_img     = ImageTk.PhotoImage(Image.open(str(SCRIPTDIR/'end.png')))


from collections import deque
from threading import Thread, Lock, Semaphore

class ImageLoadingQueue:
    # public methods, run on main thread

    # waiting :: [(path, info)]
    def __init__(self, waiting, min, max, debug=False):
        self.waiting = waiting # only internal methods can mutate
        self.waiting.reverse()
        self.min = min # read only
        self.max = max # read only <- TODO can be adjusted?

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
                img = ImageTk.PhotoImage(Image.open(str(path)))
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

front_queue = ImageLoadingQueue(files, 2, 10)
back_queue  = ImageLoadingQueue([], 2, 3)

front_queue.run()
back_queue.run()


lab = Label(image=start_img)
lab.grid(row=0,column=1,columnspan=3)

last_key = None
key_released = True
started = False

import subprocess

def show_current(start=False):
    #print(f"show_current")
    if not started:
        img = start_img
        title = f"Topho {version}"
    else:
        ret = front_queue.get(block=False, pop=False)
        if ret is None: # no more data
            img = end_img
            title = "END"
        elif not ret: # loading
            img = loading_img
            title = "LOADING"
        else:
            img = ret[0]
            title = str(ret[2]) + " " + ret[1].name

    if img is None: # unrecognized type
        img = unrecog_img
    elif not img: # image broken..
        img = broken_img
    elif img == 'video':
        img = video_img
        subprocess.Popen(["mpv", "--loop=inf", ret[1]])

    lab.config(image=img)
    lab.grid(row=0,column=1,columnspan=3)
    root.title(title)

def key_press(e):
    global last_key, key_released, started
    if e.char == last_key and not key_released: return
    last_key, key_released = e.char, False

    if last_key == 'q':
        #print("quit")
        root.destroy()
        return

    if last_key == ' ' and not started:
        #print("start")
        started = True
        show_current()
        return

    if not started: return

    elif last_key == 'r':
        #print("reload")
        show_current()
        
    elif '0' <= last_key and last_key <= '9':
        #print("do")
        ret = front_queue.get(block=False)
        if ret: # no more data, do nothing
            img, orig_path, _ = ret
            back_queue.put((img, orig_path, int(last_key)))
        show_current()

    elif last_key == 'u':
        #print("undo")
        ret = back_queue.get()
        if ret is None: # at the start
            started = False
            show_current()
        elif not ret: # loading
            # FIXME
            lab.config(image=loading_img)
            lab.grid(row=0,column=1,columnspan=3)
        else:
            front_queue.put(ret)
            show_current()

    elif last_key == 'U' or last_key == ' ':
        #print("redo")
        ret = front_queue.get(block=False)
        if ret: # no more data, do nothing
            back_queue.put(ret)
        show_current()


def key_release(e):
    global last_key, key_released
    key_released = True

root.bind('<KeyPress>', key_press)
root.bind('<KeyRelease>', key_release)

root.mainloop()

front_queue.quit()
back_queue.quit()


result = back_queue.flush()

# %%

dst_dirs = [] # :: [ (path, created_by_program?) ]

for i in range(10):
    dirpath = target_dir / str(i)
    if dirpath.exists():
        while dirpath.exists() and not dirpath.is_dir():
            dirpath = target_dir / (dirpath.name + "_")
    if not dirpath.exists():
        dirpath.mkdir()
        dst_dirs.append((dirpath,True))
    else:
        dst_dirs.append((dirpath,False))

for cur, dir in result:
    dst = dst_dirs[dir][0] / cur.name
    if not cur.exists():
        print(str(cur) + " is missing!")
        continue
    if dst.exists():
        print(str(dst) + " exists!")
        continue
        # FIXME
    cur.replace(dst)
    #print("moving " + str(cur) + " to " + str(dst) + "!")

for dirpath, created in dst_dirs:
    if not created: continue
    try:
        dirpath.rmdir()
    except OSError:
        # error occures when dir is nonempty
        # we only want to remove unneccessary empty dirs that we created
        pass

