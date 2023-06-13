import subprocess
import tempfile
import sys

from misc import *
from selector_view import SelectorView

def run_select(args): #, should_dump): # TODO implement this when piping ochestration implemented

    # TODO implement this when cache manager become available
    #if args.source[0] == 'dir':
    temp_dir = None
    arx_proc = None
    source_dir = args.source[1]
    # else:
    #     temp_dir = Path(tempfile.mkdtemp(prefix=str(args.source[1]), dir='.'))
    #     arx_proc = subprocess.Popen([str(args.arx), 'x', '-target:name', args.source[1], str(temp_dir)])
    #     source_dir = temp_dir / args.source[1].stem

    # TODO if the source is archived, we only gain time from SelectorView loading ... can't we do better?

    view = SelectorView(args.maxw, args.maxh,
        #lambda path: subprocess.Popen([str(args.player), "--loop=inf", str(path)]).wait(), # FIXME waiting prevents the program from updating image
        lambda path: subprocess.Popen([str(args.player), "--loop=inf", str(path)]),
        SCRIPTDIR.parent/"resources")

    # TODO implement this when cache manager become available
    # if arx_proc is not None:
    #     arx_proc.wait()

    KNOWN_EXTS = VIDEO_EXTS | IMAGE_EXTS
    supported_files = (
        path
        for path
        in source_dir.glob('**/*')
        if not path.is_dir() and path.suffix[1:] in KNOWN_EXTS
    )

    # FIXME
    ignored_files = list(
        path
        for path
        in source_dir.glob('**/*')
        if not path.is_dir() and not path.suffix[1:] in KNOWN_EXTS
    )

    view.load(supported_files, (args.frontq_min, args.frontq_max, args.backq_min, args.backq_max))
    selections = view.run()

    # TODO implement this when piping ochestration implemented
    #if should_dump:
    #    if args.selections is not None:
    f = open(args.selections, "wt")
    #    else:
    #        f = sys.stdout

    dump_selection(f, source_dir, selections)
    f.close()

    # FIXME
    if not view.contd:
        print("no commit, nothing happed!")
        if temp_dir is not None:
            shutil.rmtree(temp_dir)
        sys.exit()

    return # view.contd, selections # TODO implement this when piping ochestration implemented

from handy_format import format_name

def run_apply(args):
    trashcan_namef = "{modified}[-[{hier:]-]!}{name}_{dup}"

    with open(args.selections, "rt") as f: # TODO what if fails?
        selections_dump = load_selection(f)
    source_dir = Path(selections_dump["source_dir"]) # TODO do it in load_selections
    selections = selections_dump["selections"]

    mapping = [] # [ (src, dst) ]
    dsts = set()
    
    exists = lambda path: path.exist() or path in dsts

    for i, (src, dir) in enumerate(selections):
        src = Path(src) # TODO do it in load_selections
        # if dir is None: # skipped files
        #     skipped.append(dir)
        #     continue

        if dir == 0: # this is a trashcan
            dst, j = format_name(trashcan_namef, i, src, source_dir, args.target/str(dir)) # exists = lambda path: check if exists in dsts
        else:
            dst, j = format_name(args.name_format, i, src, source_dir, args.target/str(dir))

        mapping.append((src,dst))
        dsts.add(dst)

    f = open(args.mappings, "wt")

    # TODO extract common parent wd? for readability & safety check
    dump_mapping(f, mapping)
    f.close()


import shutil
from time import sleep
#import tempfile
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

def run_commit(args):
#def organize(result, args, source_dir, temp_dir, ignored_files, START_TIME):
    temp_dir, source_dir, ignored_files = None, None, []

    with open(args.mappings, "rt") as f:
        mappings_dump = load_mapping(f)

    mappings = mappings_dump['mappings']

    target_created_root = args.target
    while target_created_root != Path('.') and not target_created_root.parent.exists():
        target_created_root = target_created_root.parent

    leave_crumbs(args.target)
    args.target.mkdir(parents=True, exist_ok=True)

    dst_dirs = [] # :: [ (path, created_by_program?) ]

    for i in range(10):
        dirpath = args.target / str(i)
        if dirpath.exists():
            while dirpath.exists() and not dirpath.is_dir():
                dirpath = args.target / (dirpath.name + "_")
        if not dirpath.exists():
            dirpath.mkdir()
            dst_dirs.append((dirpath,True))
        else:
            dst_dirs.append((dirpath,False))

    # files couldn't be moved
    remaining = [] # :: [(reason, idx, dup, path, dir, note)]
    skipped = []

    # FIXME i keeps increasing for skippedd, trashcaned, remaining files
    for src, dst in mappings:
        if not src.exists():
            remaining.append(('MISSING', src))
            continue

        if dst.exists():
            remaining.append(('DUP', dst))
            continue

        if args.dry:
            print(("copying " if args.keep else "moving ") + str(src) + " to " + str(dst) + "!")
            continue

        try:
            if args.keep:
                if not dst.parent.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    sleep(args.filesystem_latency) # wait for filesystem update
                shutil.copy2(src, dst)
            else:
                src.replace(dst)
                # FIXME if target subdir not exist?

        except OSError as e:
            remaining.append(('OS', i, src, dst, repr(e)))

    if remaining:
        print("Remainings!")
        print(remaining)
    else:
        print(f"All {len(mappings)} files have been {'copied' if args.keep else 'moved'} properly.")

    # remove and restore dst_dir if possible
    try_rmdir_rec(args.target)
    collect_crumbs(args.target)

    # remove created target parents if possible
    target = args.target
    while target_created_root != target:
        try: target.rmdir()
        except OSError: break
        target = target.parent

    try: target.rmdir()
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