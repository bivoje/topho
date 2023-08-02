import subprocess

from misc import *
from selector_view import SelectorView


def run_select(source_dir, args, dummy=False):
    if args.player is None: raise TophoError("video player not provided")
    if args.arx    is None: raise TophoError("un-archiver not provided")

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

    if dummy:
        sels = [ (p, i%10) for i, p in enumerate(supported_files) ]
        view.contd = True
    else:
        view.load(supported_files, (args.frontq_min, args.frontq_max, args.backq_min, args.backq_max))
        sels = view.run()

    selections = []
    for (path, sel) in sels:
        assert str(path).startswith(str(source_dir))
        path = str(path)[len(str(source_dir))+1:]
        selections.append((path, sel))

    return selections if view.contd else None


from handy_format import format_name

def run_map(selections, source_dir, target_dir, name_format):
    trashcan_namef = "{modified}[-[{hier:]-]!}{name}_{dup}"
    assert not target_dir.exists() or target_dir.is_dir()

    mapping = [] # [ (src, dst) ]
    dsts = set()

    exists = lambda path: (target_dir / path).exists() or path in dsts

    for i, (src, dir) in enumerate(selections):
        # TODO if dir is None: # skipped files
        #     skipped.append(dir)
        #     continue

        namef = trashcan_namef if dir == 0 else name_format
        dst, j = format_name(namef, i, src, dir, source_dir, exists)

        mapping.append((src,dst))
        dsts.add(dst)

    return mapping


import shutil
from time import sleep

# no more file
def run_commit(mapping, source_dir, target_dir, args):
    temp_dir, ignored_files = None, []

    target_dir.mkdir(parents=True, exist_ok=True)

    # files couldn't be moved
    remaining = [] # :: [(reason, idx, dup, path, dir, note)]
    skipped = []

    for src_, dst_ in mapping:
        src, dst = source_dir / src_, target_dir / dst_

        if not src.exists():
            remaining.append(('MISSING', src_, dst_, ""))
            continue

        if dst.exists():
            remaining.append(('DUP', src_, dst_, ""))
            continue

        if args.dry:
            print(("copying " if args.keep else "moving ") + str(src) + " to " + str(dst) + "!")
            continue

        try:
            if not dst.parent.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                sleep(args.filesystem_latency) # wait for filesystem update
            if args.keep: shutil.copy2(src, dst)
            else: src.replace(dst)

        except OSError as e:
            remaining.append(('OS', src_, dst_, repr(e)))

    return remaining