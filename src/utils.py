from misc import *

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