#%%
import argparse
from pathlib import Path
from ctypes import windll

VERSION = "1.0.0"
SCRIPTDIR = Path(__file__).parent

def positive_int(s):
    try:
        x = int(s)
        assert x > 0
        return x
    except:
        raise argparse.ArgumentTypeError(f"invalid positive int value: '{s}'")

def existing_directory(s):
    try:
        path = Path(s)
        assert path.exists() and path.is_dir()
        return path
    except:
        raise argparse.ArgumentTypeError(f"non existing directory: '{s}'")

parser = argparse.ArgumentParser(prog='Topho', description='Minimallistic utility for manual image organizing')
parser.add_argument('source_dir', type=existing_directory, help='path of image directory to organize')
parser.add_argument('target_dir', type=existing_directory, help='path of directory to store organized images', default=Path.cwd(), nargs='?') #nargs='?' makes this positional argument optional
parser.add_argument('--version', '-v', action='version', version=f'%(prog)s {VERSION}')
parser.add_argument('--dry', '-n', dest='dry', action='store_true', help="don't actually move files, only pretend organizing")
parser.add_argument('--maxw', type=positive_int, default=windll.user32.GetSystemMetrics(0)*0.8, help='maximum width of image, defaults to screen width * 0.8')
parser.add_argument('--maxh', type=positive_int, default=windll.user32.GetSystemMetrics(1)*0.8, help='maximum height of image, defaults to screen height * 0.8')
parser.add_argument('--frontq_min', type=positive_int, metavar='FQm', default=3, help='minimum # of images pre-loaded, increase if forward loading is too slow. default=3')
parser.add_argument('--frontq_max', type=positive_int, metavar='FQM', default=10, help='maximum # of images kept loaded when un-doing, increase if you frequently undo & redo. default=10')
parser.add_argument('--backq_min',  type=positive_int, metavar='BQm', default=3, help='minimum # of images loaded for un-doing, increase if backward loading is too slow. default=3')
parser.add_argument('--backq_max',  type=positive_int, metavar='BQM', default=5, help='maximum # of images kept loaded after organizing, increase if you frequently undo & redo. default=5')
args = parser.parse_args()
#args = parser.parse_args(['images', '--dry'])

# %%
from tkinter import *
from utils import *

root = Tk()
root.title(f"Topho {VERSION}")

# FIXME for some reason, can't load image from main thread... :/
# default_img = front_queue()[0]
blank_img   = ImageTk.PhotoImage(Image.new('RGB', (500, 500)))
unrecog_img = load_tk_image(SCRIPTDIR/'unrecognized.png', args.maxw, args.maxh)
loading_img = load_tk_image(SCRIPTDIR/'loading.png', args.maxw, args.maxh)
broken_img  = load_tk_image(SCRIPTDIR/'broken.png', args.maxw, args.maxh)
video_img   = load_tk_image(SCRIPTDIR/'video.png', args.maxw, args.maxh)
start_img   = load_tk_image(SCRIPTDIR/'start.png', args.maxw, args.maxh)
end_img     = load_tk_image(SCRIPTDIR/'end.png', args.maxw, args.maxh)

# %%

files = list((path,0) for path in args.source_dir.iterdir() if not path.is_dir())

front_queue = ImageLoadingQueue(files, args.frontq_min, args.frontq_max, args.maxw, args.maxh)
back_queue  = ImageLoadingQueue([], args.backq_min, args.backq_max, args.maxw, args.maxh)

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
        title = f"Topho {VERSION}"
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
    dirpath = args.target_dir / str(i)
    if dirpath.exists():
        while dirpath.exists() and not dirpath.is_dir():
            dirpath = args.target_dir / (dirpath.name + "_")
    if not dirpath.exists():
        dirpath.mkdir()
        dst_dirs.append((dirpath,True))
    else:
        dst_dirs.append((dirpath,False))

for cur, dir in result:
    if dir == 0: continue
    dst = dst_dirs[dir][0] / cur.name
    if not cur.exists():
        print(str(cur) + " is missing!")
        continue
    if dst.exists():
        print(str(dst) + " exists!")
        continue
        # FIXME
    if args.dry:
        print("moving " + str(cur) + " to " + str(dst) + "!")
    else:
        cur.replace(dst)

for dirpath, created in dst_dirs:
    if not created: continue
    try:
        dirpath.rmdir()
    except OSError:
        # error occures when dir is nonempty
        # we only want to remove unneccessary empty dirs that we created
        pass