import sys
import tkinter.filedialog
import tkinter.simpledialog

import command
from handy_format import *
from arg_parser import get_parser
from utils import *
from misc import TophoError

START_TIME = HandyTime(datetime.now(timezone.utc).astimezone())

# TODO selector_view shortcut to find "next unselected"

#args = get_parser(START_TIME).parse_args()
args = get_parser(START_TIME).parse_args([
    "-c=select",
        "--source", "images.zip",
        "--player", "C:\\Program Files\\mpv-x86_64-20230312-git-9880b06\\mpv.exe",
        "--selections", "selections1.json",
    # "-c=map",
    #     "--target", "this/dir",
    #     "--name_format", "{hier._1}{name}",
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

    if cmd_flags & 1 and not args.source:
        sel = tkinter.simpledialog.SimpleDialog(None, text="choose source type", buttons=["archive", "directory"], title="source type").go()
        if sel == 0:
            src = tkinter.filedialog.askopenfilename(
                initialdir="/", title="Select an archived file",
                filetypes=(("archive files", ' '.join('.'+ext for ext in ARXIV_EXTS)), ("all files", "*.*")),
            )
            srct = 'arx'

        else:
            src = tkinter.filedialog.askdirectory(
                initialdir="/", title="Select a directory",
                mustexist=True,
            )
            srct = 'dir'

        if src == '': # canceled
            TophoError("Quitting on command - no source")

        args.source = (srct, Path(src))

    # RESTORE? SOURCE
    source_dir = None
    if cmd_flags & 1:
        stdin_ignored = True

        if args.source[0] == 'dir':
            source_dir = args.source[1]
        else:
            source_dir = get_cachedir(args.source[1], args.arx, START_TIME)

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
            dump_selection(f, source_dir, selections) # TODO what if fails?

        if args.selections:
            assert(f)
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
        source_dir = selections_dump["source_dir"]
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
            assert(f)
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

    # TODO remove source_dir if it was cache && the orig archive

try:
    run(args)
except TophoError as e:
    print(f"topho: {e}")
    exit(1)
    # TODO store selections or mappings before exiting when not stored (e.g. dup while commit, etc) -> automatically uses the most recent one when --continue-from arg is omitted