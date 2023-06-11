from misc import *

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
# TODO make this one as middle production file, not a log file
# and commit in separate process
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

from handy_format import format_name


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