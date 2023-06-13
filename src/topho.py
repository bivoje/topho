import command
from handy_format import *
from arg_parser import get_parser
from utils import *

START_TIME = HandyTime(datetime.now())

#args = get_parser(START_TIME).parse_args()
args = get_parser(START_TIME).parse_args([
    "-c=select",
         "--source", "test_images", #"images.zip",
         "--player", "C:\\Program Files\\mpv-x86_64-20230312-git-9880b06\\mpv.exe",
         # TODO skip (default) player validity check when not used
        "--selections", "selections.json",
    "-c=apply",
        "--target", "this/dir",
        "--name_format", "{hier._1}{name}",
        "--mappings", "mappings.json",
    "-c=commit",

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


# # %%
# if args.retry:
#     if args.retry == '-':
#         remaining, cwd, args_ = load_remainings(sys.stdin)
#     else:
#         with open(args.retry, "rt") as f:
#             remaining, cwd, args_ = load_remainings(f)
    
#     args_.dry = args.dry
#     args_.logfile = args.logfile.absolute()
#     args_.filesystem_latency = args.filesystem_latency

#     os.chdir(cwd)

#     result = []
#     for reason, idx, dup, path, dir, note in remaining:
#         result.append((idx, (path, dir))) # dup, reason, note ignored.

#     source_dir = args_.source

#     # FIXME temp_dir=None (consider source_dir is not temporary) 
#     # then ignored_files=[] is never used anyway and source_dir will not be removed
#     # this is error-prone interface, need to change later
#     organize(result, args_, source_dir, None, [], START_TIME)

#     sys.exit(0)


# TODO if source or target is empty, we query the user in GUI
if args.target is None:
    args.target = Path('.')


if 'select' in args.command:
    # TODO implement this when piping ochestration implemented
    #piping_selections = args.selections is None and 'apply' in args.command
    #should_continue, selections = command.run_select(args, not piping_selections)
    command.run_select(args)
    #if not should_continue: exit(0)

if 'apply' in args.command:
    command.run_apply(args)

if 'commit' in args.command:
    command.run_commit(args)
