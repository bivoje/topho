# %%
from datetime import datetime, timezone
from pathlib import Path
from utils import *
import os
import sys

# little bit tricky since 'path' already contain parent directory information,
# yet the caller have to re-assemble the returned filename with parent dir.
# might be clear if format_name was given only the orig filename or returned
# the whole path.
# But to check for directory traversing injection, we have to return only the
# filename, while we'd like to utilize 'Path's stem & suffix feature (Path.name
# returns a string)
def format_name(formstr, source_dir, path, index, dup):
    if path.exists():
        size = HandyInt(os.path.getsize(path)),
        created  = HandyTime(datetime.fromtimestamp(os.path.getctime(path)).astimezone())
        modified = HandyTime(datetime.fromtimestamp(os.path.getmtime(path)).astimezone())
        accessed = HandyTime(datetime.fromtimestamp(os.path.getatime(path)).astimezone())
    else:
        size = HandyInt(2**(6+index*4)),
        created  = HandyTime(datetime.fromtimestamp(0,tz=timezone.utc).astimezone())
        modified = HandyTime(datetime(2013,6,5,21,54,57).astimezone())
        accessed = HandyTime(datetime(2054,6,8,4,13,26).astimezone())

    return formstr.format(
        index = HandyInt(index),
        name = HandyString(path.stem),
        srcdir = HandyString(str(source_dir)),
        size = size,
        created  = created,
        modified = modified,
        accessed = accessed,
        dup = HermitDup(dup, dup),
    ) + path.suffix


# %%
import argparse
import shutil
import subprocess
from ctypes import windll

VERSION = "1.1.0"
SCRIPTDIR = Path(__file__).parent
START_TIME = HandyTime(datetime.now())

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

def writable_file(s):
    if s == '-': return '-'
    try:
        path = Path(s)
        assert not path.is_dir()
        assert not path.exists() or os.access(s, os.W_OK)
        return path
    except:
        raise argparse.ArgumentTypeError(f"not a writable path: '{s}'")

def executable(s):
    try:
        ss = shutil.which(s); assert ss
        path = Path(ss); assert path.exists() and not path.is_dir()
        #assert os.access(path, os.X_OK); shutil.which already checked X_OK
        # but still non-executable files could have X_OK.. for some reason :P

        proc = subprocess.Popen([str(path), '-V'], stdout=subprocess.PIPE)
        stdout, _ = proc.communicate(timeout=1)
        proc.kill()
        assert stdout.startswith(b'mpv ')

        return path
    except:
        raise argparse.ArgumentTypeError(f"not a valid mpv executable: '{s}'")

# Handy* formatters are statically error checked. <- run once, run always.

# furthermore, all the characters generated by Handy*.__format__ is either a digit, alphabet,
# one of "+-T:", slice of given string or thoes already present in format string.
# only valid fileapth (source_dir and filenames) are given as string, already being valid path-characters.
# characters in format string are easily validated in static time.
# any other characters (alphanum +-T:) are also valid path-characters.

# also, since '/', '\' can only come from format string literals, it is easy to check if there
# is directory-change-injection

def nameformat(s):
    try:
        # SCRIPTDIR/'end.png' is guaranteed to exist
        ret = format_name(s, SCRIPTDIR, SCRIPTDIR/'end.png', 0, 1)
        if '/' in ret or '\\' in ret:
            raise argparse.ArgumentTypeError("can't use '\\' or '/' in filenames")
# if we verify there's no '/' or '\', we can be sure'
        return s
    # KeyError when accessing non-existing variable
    # AttributeError when accessing invalid attr of HandyTime
    # ValueError for any other formatting error
    except KeyError as e:
        raise argparse.ArgumentTypeError(f"no variable named {str(e)} provided")
    except (AttributeError, ValueError) as e:
        raise argparse.ArgumentTypeError(str(e))

# https://stackoverflow.com/a/52025430
class RawTextArgumentDefaultsHelpFormatter(
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawTextHelpFormatter
    ):
        pass

parser = argparse.ArgumentParser(prog='Topho',
    formatter_class=RawTextArgumentDefaultsHelpFormatter,
    description='Minimallistic utility for manual image organizing',
    epilog='''
NAMEF:
    You can describe new name for moved file using python style formating.
    For example, giving --name_format="{index}th-image-{name}__{size}bytes"
    converts "nyancat.gif" to "1th-image-nyancat__1038bytes.gif".
    See following sections for available formatting options and variables.

NAMEF variables:
    index    :int  - enumeration, starting from 0
    name     :str  - original name of the file
    srcdir   :str  - parent directory of the file, same as <source_dir>
    size     :int  - size of the file in bytes
    created  :time - file creation time
    modified :time - file modification time
    accessed :time - file access time
    dup      :dup  - enumeration among duplicated names, starting from 0

NAMEF formatting:
    Before anything, note that only attribute access is allowed for variables,
    which means "{index*2}" is cannot be done. So we provide some attribute
    extension for ease of handling variables.

    For integer types, additional arithmetic attributes are provided as well
    as basic integer formatting syntax. You can do (asssuming index=9)
    - .p<n>, .t<n> for addition
      "{index.p20}" == '29'
    - .m<n> for subtraction
      "{index.m10}" == '-1'
    - .x<n>, .X<n> for multiplication
      "{index.x3}" == '27'
    - .d<n> for integer division
      "{index.d2}" == '4'
    - .r<n>, .l<n> for remainder (always positive)
      "{index.l5}" == '4'
    - mixture of all
      "{index.p3.x2.4}" == '6'
    - with integer format_spec
      "{index.p3.x2.4:+03}" == '+006'

    For string types, start-end slicing attributes are provided along with other
    basic string formatting syntax. You can do (assuming name=asdf)
    - ._<n> for maxcap length, same as str[:n]
      "{name._3}" == 'asd'
    - ._<n>_<m> to take range [n, <m>), same as str[n:m]
      "{name._1_3}" == 'sd'
    - indexing from behind, use 'm' prefix instead of '-' to indicate negative
      "{name._1_m1}" == 'sd'
    - complex mixture example
      "=={name._3:#^7}---" == '==##asd##---'

    For time types, you can use strftime format in format_spec region.
    See https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
    for more detailed explanations. Examples follows..
    - default formatting shows iso-8601 date
      "{created}" == '2022-08-02'
    - by specifying 'iso' as format you get full iso-8601 representation
      "{created:iso}" == '2022-08-02T07:23:45+0900'
    - accessing 'utc' attribute gives datetime in UTC
      "{created.utc:iso}" == '2022-08-01T22:23:45+0000'
    - all attributes of python datatime struct supported
      "{created.day:03}" == '002'
    - strftime style formatting
      "{created:%Y_%S}" == '2022_45'

    'dup' type is similar to 'int' type, all arithmetic attbributes are
    provided but has extended format spec. Normal integer format spec
    is may preceeded by enclosure specifier of format "<prefix>/<suffix>/".
    If enclosure specifier exists dup acts in hermit mode, expose itself
    (and enclosure) only if dup > 0.
    For example, if there are only 1 file created on 2022-08-02, the
    formatstring "{created}{dup.x2.m1:==(/)/0^3}" simply yields '2022-08-02'.
    But if there are 3 of them, they will be renamed as
    '2022-08-02', '2022-08-02==(010)', '2022-08-02==(030)' in sorted order.
    Note that hermit mode depends on 'dup' itself not 'dup.x2.m1'.
    If format_spec is empty, you can omit trailing '/', like "{dup:(/)}"
''')

parser.add_argument('source_dir', type=existing_directory,
    help='path of image directory to organize')
parser.add_argument('target_dir', type=existing_directory, default=Path('.'), nargs='?',
    help='path of directory to store organized images')
    #nargs='?' makes this positional argument optional https://stackoverflow.com/a/4480202
parser.add_argument('--version', '-v', action='version', version=f'%(prog)s {VERSION}')
parser.add_argument('--dry', '-n', dest='dry', action='store_true',
    help="don't actually move files, only pretend organizing")
parser.add_argument('--maxw', type=positive_int, default=int(windll.user32.GetSystemMetrics(0)*0.8),
    help='maximum width of image, defaults to screen width * 0.8')
parser.add_argument('--maxh', type=positive_int, default=int(windll.user32.GetSystemMetrics(1)*0.8),
    help='maximum height of image, defaults to screen height * 0.8')
parser.add_argument('--name_format', type=nameformat, metavar='NAMEF', default='{name}',
    help="python style formatstring for moved file names, see <NAMEF> section")
parser.add_argument('--test_names', type=Path, nargs='*',
    help='if provided, apply name_format on this filename, print then exits')
parser.add_argument('--logfile', type=writable_file, default="topholog.txt",
    help='path to log file where unmoved file list will be written')
parser.add_argument('--mpv', type=executable, metavar='MPVPATH', default="mpv.exe",
    help='path to invoke mpv player executable')
    # '--mpv mpv' resolved to 'mpv.COM' which prints some info to stdout by default
    # while 'mpv.exe' doesn't.
parser.add_argument('--frontq_min', type=positive_int, metavar='FQm', default=3,
    help='minimum # of images pre-loaded, increase if forward loading is too slow')
parser.add_argument('--frontq_max', type=positive_int, metavar='FQM', default=10,
    help='maximum # of images kept loaded when un-doing, increase if you frequently undo & redo')
parser.add_argument('--backq_min',  type=positive_int, metavar='BQm', default=3,
    help='minimum # of images loaded for un-doing, increase if backward loading is too slow')
parser.add_argument('--backq_max',  type=positive_int, metavar='BQM', default=5,
    help='maximum # of images kept loaded after organizing, increase if you frequently undo & redo')
args = parser.parse_args()
#args = parser.parse_args("images --dry".split())

if args.test_names:
    rets = {}
    for i, test_name in enumerate(args.test_names):
        ret_ = format_name(args.name_format, args.source_dir, test_name, i, 0)
        j = rets.get(ret_, 0)
        if j > 0:
            ret = format_name(args.name_format, args.source_dir, test_name, i, j)
        else: ret = ret_
        rets[ret_] = j+1
        print(ret)
    sys.exit(0)

# %%
from tkinter import *

root = Tk()
root.title(f"Topho {VERSION}")

# FIXME for some reason, can't load image from main thread... :/
# default_img = front_queue()[0]
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
commit = False

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
        subprocess.Popen([str(args.mpv), "--loop=inf", ret[1]])

    lab.config(image=img)
    lab.grid(row=0,column=1,columnspan=3)
    root.title(title)

def key_press(e):
    global last_key, key_released, started, commit
    if e.char == last_key and not key_released: return
    last_key, key_released = e.char, False

    if last_key == '\x1b':
        #print("quit")
        root.destroy()
        return

    if last_key == 'c':
        #print("commit")
        commit = True
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
result.reverse()


# %%
if not commit:
    print("no commit, nothing happed!")
    sys.exit()

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

# to keep dup-counts
names = [{}]*10

for i, (cur, dir) in enumerate(result):
    if dir == 0: continue

    if not cur.exists():
        remaining.append(('MISSING', i, j, cur, dir, ''))
        continue

    try:
        name_ = format_name(args.name_format, args.source_dir, cur, i, 0)
        j = names[dir].get(name_, 0)
        if j > 0:
            name = format_name(args.name_format, args.source_dir, cur, i, j)
        else: name = name_
        names[dir][name_] = j+1

    except Exception as e:
        # this is unlikely to happen, but if it does, make sure other files get moved safely
        print(f"while moving '{cur}' to '{dst_dirs[dir][0]}', ")
        print(e)
        print("please report this to the developer!")
        remaining.append(('FORMAT', i, j, cur, dir, repr(e)))
        continue

    dst = dst_dirs[dir][0] / name

    if dst.exists():
        print(dst)
        remaining.append(('DUP', i, j, cur, dir, ''))
        continue

    if args.dry:
        print("moving " + str(cur) + " to " + str(dst) + "!")
        continue

    try:
        cur.replace(dst)
    except OSError as e:
        remaining.append(('OS', i, j, cur, dir, repr(e)))

def write_remainings(f):
    f.write(f"#Topho {VERSION} {START_TIME:iso}")
    f.write(f"#{args.source_dir.absolute()}\n")
    f.write(f"#{args.target_dir.absolute()}\n")
    f.write(f"#{args.name_format}\n")
    f.write(f"#REASON\tINDEX\tDUP\tSOURCE\tDECISION\n")
    for reason, idx, dup, path, dir, note in remaining:
        f.write(f"{reason}\t{idx}\t{dup}\t{path}\t{dir}\t{note}\n")

if remaining:
    print(f"{len(remaining)} / {len(result)} files could not be moved, detailed reasons are recorded.")
    if args.logfile == '-':
        write_remainings(sys.stdout)
    else:
        try:
            with open(args.logfile, "at") as f:
                write_remainings(f)
        except:
            print("couldn't open the logfile")
            write_remainings(sys.stdout)
else:
    print(f"All {len(result)} files have been moved properly.")

for dirpath, created in dst_dirs:
    if not created: continue
    try:
        dirpath.rmdir()
    except OSError:
        # error occures when dir is nonempty
        # we only want to remove unneccessary empty dirs that we created
        pass