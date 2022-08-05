# %%
from datetime import datetime, timezone
from pathlib import Path
from utils import *
import os
import sys

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
import argparse
import shutil
import subprocess
from ctypes import windll

VERSION = "2.0.0"
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

def existing_directory_or_archive(s):
    path = Path(s)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"non existing source: '{s}'")

    if path.is_dir():
        return ('dir', path)

    if path.suffix[1:] in ARXIV_EXTS and os.access(path, os.R_OK):
        return ('arx', path)

    raise argparse.ArgumentTypeError(f"source is neither directory or reable archive file: '{s}'")

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

        # proc = subprocess.Popen([str(path), '-V'], stdout=subprocess.PIPE)
        # stdout, _ = proc.communicate(timeout=1)
        # proc.kill()
        # assert stdout.startswith(b'mpv ')

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
    if '/' in s or '\\' in s: # if we verify there's no '/' or '\', we can be sure'
        raise argparse.ArgumentTypeError("can't use '\\' or '/' in filenames")
    try:
        ret = s.format( # generate with random
            index = HandyInt(1),
            name = HandyString("Bapanada"),
            hier = HandySlice(["this", "dir"]),
            size = 3012,
            created  = HandyTime(datetime(1970,1,3).astimezone()),
            modified = HandyTime(datetime(1970,1,3).astimezone()),
            accessed = HandyTime(datetime(1970,1,3).astimezone()),
            dup = HermitDup(1),
        )
        return s
    # KeyError when accessing non-existing variable
    # AttributeError when accessing invalid attr of HandyTime
    # ValueError for any other formatting error
    except KeyError as e:
        raise argparse.ArgumentTypeError(f"no variable named {str(e)} provided")
    except (AttributeError, ValueError) as e:
        raise argparse.ArgumentTypeError(str(e))
    except Exception as e:
        # other kind of exceptions are an error in the code not namestr
        # but argparse catches them all and hide the message.
        # so we print it here for debugging purpose
        print("BUG! report to the developer!", repr(e))
        raise e

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
    size     :int  - size of the file in bytes
    hier     :slice- list of parent directories from source_dir, inclusive
    created  :time - file creation time
    modified :time - file modification time
    accessed :time - file access time
    dup      :dup  - enumeration among duplicated names, starting from 0

NAMEF formatting:
    Before anything, note that only attribute access is allowed for variables,
    which means "{index*2}" is cannot be done. So we provide some attribute
    extension for ease of handling variables.

    For integer type, additional arithmetic attributes are provided as well
    as basic integer formatting syntax. You can do (asssuming index=9)
    - .p<n>, .t<n> for addition
      "{index.p20}" == '29'
    - .m<n> for subtraction
      "{index.m10}" == '-1'
    - .x<n>, .X<n> for multiplication
      "{index.x3}" == '27'
    - .d<n> for integer division
      "{index.d2}" == '4'
    - mixture of all
      "{index.p3.x2.4}" == '6'
    - with integer format_spec
      "{index.p3.x2.4:+03}" == '+006'

    For slice type, start-end slicing attributes are provided. format spec can be
    preceded with a seperator as '<sep>!<spec>' which will be used to join slice elements.
    If spereator is omitted, it defaults to '' or '\\' for 'hier' variable.
    <spec> is basic python formatter, applys element-wisely. Each formatted result
    then joined by <sep>. string types are simliar to slice type but <spec> applys to
    the whole string. You can do (assuming name=asdf)
    - ._<n> for starting index, same as str[n:]
      "{slice._2}" == 'df'
    - .__<m> for ending index, same as str[:m]
      "{slice.__3}" == 'asd'
    - ._<n>_<m> to take range [n, m), same as str[n:m]
      "{name._1_3}" == 'sd'
    - indexing from behind, use 'm' prefix instead of '-' to indicate negative
      "{name._1_m1}" == 'sd'
    - complex mixture example
      "=={name._3:#^7}---" == '==##asd##---'

    'hier' is slice variable consisting of directory names from source_dir to
    the file. '' element is at the end to add trailing seperator.
    Assume source_dir = 'images' and filepath is 'images\source\dir\y.png', then
    hier == ['images', 'source', 'dir', ''] and name == y.png,
    - simpy using with {name} to get filepath (from source_dir)
      "{hier}{name}" == 'images\source\dir\y.png'
    - use custome seperator with custom elem-wize formatting
      "{hier:-!:_<5}{name}" == 'images-source-dir__-y.png'
    - remove trailing seperator by slicing
      "{hier._1_m1}_{name}" == 'source\dir_y.png'

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
    is may preceeded by enclosure specifier of format "<prefix>!<suffix>!".
    If enclosure specifier exists dup acts in hermit mode, expose itself
    (and enclosure) only if dup > 0.
    For example, if there are only 1 file created on 2022-08-02, the
    formatstring "{created}{dup.x2.m2:==(!)!0^3}" simply yields '2022-08-02'.
    But if there are 4 of them, they will be renamed as (in sorted order)
    '2022-08-02==(-20)', '2022-08-02', '2022-08-02==(020)' '2022-08-02==(040)'.
    Note that hermit mode depends on result 'dup.x2.m2' not the original 'dup'.
    If format_spec is empty, you can omit trailing '!', like "{dup:(!)}"
''')

parser.add_argument('source', type=existing_directory_or_archive,
    help='path of image directory to organize or an archive file')
parser.add_argument('target_dir', type=Path, default=None, nargs='?',
    help='path of directory to store organized images, defaults to current directory, created if not exists')
    #nargs='?' makes this positional argument optional https://stackoverflow.com/a/4480202
parser.add_argument('--version', '-v', action='version', version=f'%(prog)s {VERSION}')
parser.add_argument('--dry', '-n', dest='dry', action='store_true',
    help="don't actually move files, only pretend organizing")
parser.add_argument('--keep', '--copy', dest='keep', action='store_true',
    help="keep the original files (copy, not move)")
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
parser.add_argument('--arx', type=executable, metavar='ARXPATH', default="Bandizip.exe",
    help='path to invoke un-archive files')
parser.add_argument('--frontq_min', type=positive_int, metavar='FQm', default=3,
    help='minimum # of images pre-loaded, increase if forward loading is too slow')
parser.add_argument('--frontq_max', type=positive_int, metavar='FQM', default=10,
    help='maximum # of images kept loaded when un-doing, increase if you frequently undo & redo')
parser.add_argument('--backq_min',  type=positive_int, metavar='BQm', default=3,
    help='minimum # of images loaded for un-doing, increase if backward loading is too slow')
parser.add_argument('--backq_max',  type=positive_int, metavar='BQM', default=5,
    help='maximum # of images kept loaded after organizing, increase if you frequently undo & redo')
args = parser.parse_args()
#args = parser.parse_args(["images.zip", "this/dir", "--name_format", "{hier._1}{name}"])

# %%

import tempfile

if args.test_names:
    source_dir = args.source[1]
    virtual_files = set()
    if args.target_dir is None or not args.target_dir.exists():
        outdir = Path('.')
        exists = lambda p: p in virtual_files
    else:
        if not args.target_dir.is_dir():
            print(f"target_dir '{args.target_dir}' is not a directory")
        outdir = args.target_dir
        exists = lambda p: p.exists() or p in virtual_files

    for i, test_name in enumerate(args.test_names):
        test_path = source_dir / test_name
        ret, _ = format_name(args.name_format, i, test_path, source_dir, outdir, exists=exists)
        virtual_files.add(ret)
        print(ret)

    sys.exit(0)

if args.target_dir is None:
    args.target_dir = Path('.')

if args.source[0] == 'dir':
    temp_dir = None
    source_dir = args.source[1]
else:
    temp_dir = Path(tempfile.mkdtemp(prefix=str(args.source[1]), dir='.'))
    arx_proc = subprocess.Popen([str(args.arx), 'x', '-target:name', args.source[1], str(temp_dir)])
    source_dir = temp_dir / args.source[1].stem


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
if temp_dir is not None:
    arx_proc.wait()

KNOWN_EXTS = VIDEO_EXTS | IMAGE_EXTS
supported_files = list(
    (path, None)
    for path
    in source_dir.glob('**/*')
    if not path.is_dir() and path.suffix[1:] in KNOWN_EXTS
)

ignored_files = list(
    path
    for path
    in source_dir.glob('**/*')
    if not path.is_dir() and not path.suffix[1:] in KNOWN_EXTS
)

front_queue = ImageLoadingQueue(supported_files, args.frontq_min, args.frontq_max, args.maxw, args.maxh)
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
            title = ('-' if ret[2] is None else str(ret[2])) + " " + ret[1].name

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

    elif last_key == 'U':
        #print("redo")
        ret = front_queue.get(block=False)
        if ret: # no more data, do nothing
            back_queue.put(ret)
        show_current()

    elif last_key == ' ':
        #print("skip")
        ret = front_queue.get(block=False)
        if ret: # no more data, do nothing
            img, orig_path, _ = ret
            back_queue.put((img, orig_path, None))
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
from time import sleep

if not commit:
    print("no commit, nothing happed!")
    if temp_dir is not None:
        shutil.rmtree(temp_dir)
    sys.exit()

target_dir_created_root = args.target_dir
while target_dir_created_root != Path('.') and not target_dir_created_root.parent.exists():
    target_dir_created_root = target_dir_created_root.parent

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
for i, (cur, dir) in enumerate(result):
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
                sleep(0.01) # wait for filesystem update
            shutil.copy(cur, dst)
        else:
            cur.replace(dst)
            # FIXME if target subdir not exist?

    except OSError as e:
        remaining.append(('OS', i, j, cur, dir, repr(e)))

def write_remainings(f):
    f.write(f"#Topho {VERSION} {START_TIME:iso} {'copy' if args.keep else 'move'}")
    f.write(f"#{args.source[1].absolute()}\n")
    f.write(f"#{args.target_dir.absolute()}\n")
    f.write(f"#{args.name_format}\n")
    f.write(f"#REASON\tINDEX\tDUP\tSOURCE\tDECISION\n")
    for reason, idx, dup, path, dir, note in remaining:
        f.write(f"{reason}\t{idx}\t{dup}\t{path}\t{dir}\t{note}\n")

if remaining:
    print(f"{len(remaining)} / {len(result)} files could not be {'copied' if args.keep else 'moved'}, detailed reasons are recorded.")
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
    print(f"All {len(result)} files have been {'copied' if args.keep else 'moved'} properly.")

# remove dst_dir if possible
for dirpath, created in dst_dirs:
    if not created: continue
    try:
        dirpath.rmdir()
    except OSError:
        # error occures when dir is nonempty
        # we only want to remove unneccessary empty dirs that we created
        pass

    try:
        dirpath.rmdir()
    except OSError:
        # error occures when dir is nonempty
        # we only want to remove unneccessary empty dirs that we created
        pass

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