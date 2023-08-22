import subprocess
import shlex

from misc import *
from selector_view import SelectorView


def run_select(source_dir, dirnames, args, dummy=False):
    if args.player is None: raise TophoError("video player not provided")

    view = SelectorView(args.maxw, args.maxh,
        #lambda path: subprocess.Popen([ tok.format(file=path) for tok in shlex.split(args.player) ]).wait(), # FIXME waiting prevents the program from updating image
        lambda path: subprocess.Popen([ tok.format(file=path) for tok in shlex.split(args.player) ]),
        dirnames, SCRIPTDIR.parent/"resources")

    KNOWN_EXTS = VIDEO_EXTS | IMAGE_EXTS
    files = (
        path
        for path
        in source_dir.glob('**/*')
        if not path.is_dir()
    )

    ignored_files   = filter(lambda p: p.suffix[1:] not in KNOWN_EXTS, files)
    supported_files = filter(lambda p: p.suffix[1:]     in KNOWN_EXTS, files)

    if args.sort_by:
        def get_meta(path, by):
            if by == 'created':
                return os.path.getctime(path)
            elif by == 'modified':
                return os.path.getmtime(path)
            elif by == 'accessed':
                return os.path.getatime(path)
            elif by == 'size':
                return os.path.getsize(path)
            elif by == 'name':
                return path.stem
            elif by == 'namelen':
                return len(path.stem)
            elif by == 'ext':
                return path.suffix
            else: assert(False)

        supported_files = list(supported_files)
        for by in reversed(args.sort_by):
            supported_files.sort(key = lambda p: get_meta(p, by[1]), reverse = not by[0])

    # TODO
    # image similarity??
    # list-preview in the bottom?
    # UI to manage pipelining


    if dummy:
        sels = [ (p, i%5 if i%4>0 else None) for i, p in enumerate(supported_files) ]
        view.contd = True
    else:
        view.load(supported_files, (args.frontq_min, args.frontq_max, args.backq_min, args.backq_max))
        sels = view.run()

    selections = []
    for (path, sel) in sels:
        assert str(path).startswith(str(source_dir))
        path = str(path)[len(str(source_dir))+1:]
        selections.append((path, sel))

    return (selections, ignored_files, view.dirnames) if view.contd else None


from handy_format import format_name

def run_map(selections, dirnames, source_dir, target_dir, name_format, discard_trash):
    trashcan_namef = "{modified}[-[{hier:]-]!}{name}_{dup}" # FIXME, is this really useful?
    assert not target_dir.exists() or target_dir.is_dir()

    mapping = [] # [ (src, dst) ]
    skipped = []
    dsts = set()

    exists = lambda path: (target_dir / path).exists() or path in dsts

    for i, (src, dir) in enumerate(selections):
        if dir is None: # skipped files
            skipped.append(src)
            continue

        namef = trashcan_namef if dir == 0 else name_format
        if dir == 0:
            if discard_trash:
                dst, j = None, 0
            else:
                dst, j = format_name(namef, i, src, "0" or str(dir), source_dir, exists)
        else:
            dst, j = format_name(namef, i, src, dirnames[dir] or str(dir), source_dir, exists)

        mapping.append((src,dst))
        dsts.add(dst)

    return mapping, skipped


import shutil
from time import sleep

# no more file
def run_commit(mapping, source_dir, target_dir, args):

    target_dir.mkdir(parents=True, exist_ok=True)

    # files couldn't be moved
    remaining = [] # :: [(reason, idx, dup, path, dir, note)]

    for src_, dst_ in mapping:
        src, dst = source_dir / src_, target_dir / dst_

        if not src.exists():
            remaining.append(('MISSING', src_, dst_, ""))
            continue

        if dst is not None and dst.exists():
            remaining.append(('DUP', src_, dst_, ""))
            continue

        if args.dry:
            print(("copying " if args.keep else "moving ") + str(src) + " to " + str(dst) + "!")
            continue

        try:

            if dst is None:
                src.unlink()
                continue

            if not dst.parent.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                sleep(args.filesystem_latency) # wait for filesystem update
            if args.keep: shutil.copy2(src, dst)
            else: src.replace(dst)

        except OSError as e:
            remaining.append(('OS', src_, dst_, repr(e)))

    return remaining