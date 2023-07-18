import sys

import command
from handy_format import *
from arg_parser import get_parser
from utils import *
from misc import TophoError

START_TIME = HandyTime(datetime.now())

#args = get_parser(START_TIME).parse_args()
args = get_parser(START_TIME).parse_args([
    "-c=select",
        #"--source", "test_images", #"images.zip",
        "--player", "C:\\Program Files\\mpv-x86_64-20230312-git-9880b06\\mpv.exe",
        # TODO skip (default) player validity check when not used
        #"--selections", "selections1.json",
    "-c=map",
        "--target", "this/dir",
        "--name_format", "{hier._1}{name}",
        #"--mapping", "mapping.json",
    # "-c=commit",

    # "--help",
])

# %%

# import tempfile

# if args.test_names:
#     source_dir = args.source[1]
#     virtual_files = set()
#     if args.target is None or not args.target.exists():
#         outdir = Path('.')
#         exists = lambda p: p in virtual_files
#     else:
#         if not args.target.is_dir():
#             print(f"target '{args.target}' is not a directory")
#         outdir = args.target
#         exists = lambda p: p.exists() or p in virtual_files

#     for i, test_name in enumerate(args.test_names):
#         test_path = source_dir / test_name
#         ret, _ = format_name(args.name_format, i, test_path, source_dir, outdir, exists=exists)
#         virtual_files.add(ret)
#         print(ret)

#     sys.exit(0)


def run(args):
    cmd_flags = 0
    for f,c in [(1, 'select'), (2, 'map'), (4, 'commit')]:
        if c in args.command: cmd_flags |= f

    if cmd_flags == 0 or cmd_flags == 5:
        raise TophoError("unacceptable command sequence")

    stdin_ignored = False

    # RESTORE? SOURCE
    if cmd_flags & 1:
        stdin_ignored = True
        if args.source:
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

        else:
            # TODO implement dialog box for source
            raise TophoError("no source")

    # RUN SELECT
    if cmd_flags & 1:
        ret = command.run_select(source_dir, args, True)
        if ret is None: # quit while selecting
            raise TophoError("Quitting on command")
        selections = ret
    else:
        selections = None

    # STORE SELECT
    if selections:
        if args.selections:
            f = open(args.selections, "wt")
        elif not cmd_flags & 2:
            f = sys.stdout
        else:
            f = None

        if f is not None:
            dump_selection(f, source_dir, selections)

        if args.selections:
            f.close()

    # RESTORE SELECT
    elif cmd_flags & 2:
        if args.selections:
            f = open(args.selections, "rt") # TODO what if fails?
        elif not stdin_ignored:
            f = sys.stdin
            stdin_ignored = True
        else:
            raise TophoError("can't restore selections")

        selections_dump = load_selection(f) # TODO what if fails?
        source_dir = Path(selections_dump["source_dir"]) # TODO do it in load_selections
        selections = selections_dump["selections"]

        if not args.selections:
            f.close()

    # TODO implement this when cache manager become available
    # if not view.contd:
    #     print("no commit, nothing happed!")
    #     if temp_dir is not None:
    #         shutil.rmtree(temp_dir)
    #     sys.exit()

    # RUN MAP
    if cmd_flags & 2:
        mapping = command.run_map(selections, source_dir, args)
    else:
        mapping = None

    # STORE MAPPING
    if mapping:
        if args.mapping:
            f = open(args.mapping, "wt")
        elif not cmd_flags & 4:
            f = sys.stdout
        else:
            f = None

        if f is not None:
            # TODO extract common parent wd? for readability & safety check
            dump_mapping(f, mapping)

        if args.mapping:
            f.close()

    # RESTORE MAPPING
    elif cmd_flags & 4:
        if args.mapping:
            f = open(args.mapping, "rt")
        elif not stdin_ignored:
            f = sys.stdin
            stdin_ignored = True
        else:
            raise TophoError("can't restore mapping")

        mapping_dump = load_mapping(f)
        mapping = mapping_dump['mapping']

        if not args.mapping:
            f.close()

    # ???
    # TODO if source or target is empty, we query the user in GUI
    if cmd_flags & 4 and args.target is None:
        args.target = Path('.')

    # RUN COMMIT
    if cmd_flags & 4:
        ret = command.run_commit(mapping, args)
    else:
        ret = None


try:
    run(args)
except TophoError as e:
    print(f"topho: {e}")
    exit(1)