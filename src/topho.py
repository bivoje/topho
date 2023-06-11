
import sys

import subprocess

from handy_format import *
from arg_parser import get_parser
from utils import *

SCRIPTDIR = Path(__file__).parent
START_TIME = HandyTime(datetime.now())

args = get_parser(START_TIME).parse_args()
#args = get_parser(START_TIME).parse_args(["images.zip", "this/dir", "--name_format", "{hier._1}{name}"])


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


# %%
if args.retry:
    if args.retry == '-':
        remaining, cwd, args_ = load_remainings(sys.stdin)
    else:
        with open(args.retry, "rt") as f:
            remaining, cwd, args_ = load_remainings(f)
    
    args_.dry = args.dry
    args_.logfile = args.logfile.absolute()
    args_.filesystem_latency = args.filesystem_latency

    os.chdir(cwd)

    result = []
    for reason, idx, dup, path, dir, note in remaining:
        result.append((idx, (path, dir))) # dup, reason, note ignored.

    source_dir = args_.source

    # FIXME temp_dir=None (consider source_dir is not temporary) 
    # then ignored_files=[] is never used anyway and source_dir will not be removed
    # this is error-prone interface, need to change later
    organize(result, args_, source_dir, None, [], START_TIME)

    sys.exit(0)


# %%
if args.target_dir is None:
    args.target_dir = Path('.')

if args.source[0] == 'dir':
    temp_dir = None
    source_dir = args.source[1]
else:
    temp_dir = Path(tempfile.mkdtemp(prefix=str(args.source[1]), dir='.'))
    arx_proc = subprocess.Popen([str(args.arx), 'x', '-target:name', args.source[1], str(temp_dir)])
    source_dir = temp_dir / args.source[1].stem


from selector_view import SelectorView

# %%
view = SelectorView(args.maxw, args.maxh, str(args.mpv), SCRIPTDIR.parent/"resources")

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

view.load(supported_files, (args.frontq_min, args.frontq_max, args.backq_min, args.backq_max))

result = view.run()
result = list(enumerate(result))

# %%

if not view.commit:
    print("no commit, nothing happed!")
    if temp_dir is not None:
        shutil.rmtree(temp_dir)
    sys.exit()

organize(result, args, source_dir, temp_dir, ignored_files, START_TIME)