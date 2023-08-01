# string format only allows attribute access & formatting. (no method calls!)
# so we need to wrap some formatting features via __getattr__ and __format__ methods.
# generally, __getattr__ returns the same class while __format__ returns string

# an error exists in a format string using Handy* features gets revealed at any attempt.
# in other words, once str.format runs without an error, you can rely on it.
# or you can say, all erros are statically caught.

from datetime import datetime, timezone

#class HandyTime(time.struct_time):
# cannot subclass directly since struc_time is c-struct internally
# https://stackoverflow.com/a/10114382
class HandyTime:
    # t = HandyTime(time.struct_time((2022,8,2,7,23,45,0,0,0)).astimezone())
    # "{t        }".format(t=t) == '2022-08-02'
    # "{t    :iso}".format(t=t) == '2022-08-02T07-23-45+0900'
    # "{t.utc:iso}".format(t=t) == '2022-08-01T22-23-45+0000'
    # "{t.day :03}".format(t=t) == '002'
    # "{t  :%Y_%S}".format(t=t) == '2022_45'
    def __init__(self, dt):
        assert isinstance(dt, datetime)
        self.datetime = dt

    def __getattr__(self, key):
        if key == 'utc':
            return self.get_utc()
        return self.datetime.__getattribute__(key)

    # https://docs.python.org/3/library/time.html#time.strftime
    def __call__(self, format):
        try:
            return self.datetime.strftime(format)
        except ValueError:
            raise ValueError(f"invalid formatting '{format}'")

    def __str__(self):
        return self.iso()

    # https://docs.python.org/3/reference/datamodel.html#object.__format__
    # "The format_spec argument is a string that contains a description of the
    #  formatting options desired. The interpretation of the format_spec
    #  argument is up to the type implementing __format__()"
    def __format__(self, format_spec):
        if format_spec == 'iso':
            return self.iso()
        if format_spec == '':
            return self('%Y-%m-%d')
        return self(format_spec)

    def iso(self):
        return self('%Y-%m-%dT%H-%M-%S%z')

    def get_utc(self):
        return HandyTime(self.datetime.astimezone(timezone.utc))


class HandySlice:
    def __init__(self, slc, sep=''):
        self.slc = slc
        self.sep = sep

    def new(self, slc):
        return HandySlice(slc, sep=self.sep)

    def __str__(self):
        return str(self.slc)

    def __repr__(self):
        return repr(self.slc)

    def __getattr__(self, key):
        def intp(s):
            try:
                return int(s) if s[0] != 'm' else -int(s[1:])
            except:
                raise ValueError("could not parse '{s}' as an index in {key}")

        if key[0:2] == '__':
            s, e = None, intp(key[1:])
        elif key[0] == '_':
            if '_' not in key[1:]:
                s, e = intp(key[1:]), None
            else:
                se = key[1:].split('_')
                if len(se) != 2:
                    raise ValueError(f"invalid slicing attribute format '{key}'")
                s, e = intp(se[0]), intp(se[1])
        else:
            raise ValueError(f"slicing attribute starts with '_' but found '{key}'")

        return self.new(self.slc[s:e])

    def __format__(self, format_spec):
        ret = format_spec.split('!', 1)
        if len(ret) == 2:
            sep, spec = ret
        else:
            sep, spec = self.sep, format_spec

        return sep.join(format(x, spec) for x in self.slc)


class HandyString(HandySlice):
    # "{s._1_3}---".format(s=HandyString('asdf')) == 'sd'
    # "=={s._3:#^7}---".format(s=HandyString('asdf')) == '==##asd##---'
    def __init__(self, slc):
        assert isinstance(slc, str)
        super(HandyString, self).__init__(slc)

    def new(self, string):
        return HandyString(string)

    # bypasses parent's formatting
    def __format__(self, format_spec):
        return format(self.slc, format_spec)

    # TODO split, replace
    # def __getattr__(self, key):
    #     if key[0] == 's':
    #         split()


class HandyInt:
    # "{n.p3.x2.d5}".format(n=HandyInt(3)) == '2'
    def __init__(self, integer):
        self.integer = integer

    def new(self, integer):
        return HandyInt(integer)

    def __getattr__(self, key):
        try:
            val = int(key[1:])
        except:
            raise ValueError(f"could not parse '{key[1:]}' as an integer in {key}")

        if key[0] == 'd':
            if val == 0:
                raise ValueError(f"can't divide with zero in '{key}'")
            ret = self.integer // val
        elif key[0] == 'p' or key[0] == 't':
            ret = self.integer + val
        elif key[0] == 'm':
            ret = self.integer - val
        elif key[0] == 'x' or key[0] == 'X':
            if val == 0:
                raise ValueError(f"use constant value 0 instead '{key}'")
            ret = self.integer * val
        elif key[0] == 'r' or key[0] == 'l':
            ret = self.integer % val
        else:
            raise ValueError(f"unrecognized integer arithmetic attribute '{key[0]}'")

        return self.new(ret)

    def __str__(self):
        return str(self.integer)

    def __format__(self, format_spec):
        return format(self.integer, format_spec)


class HermitDup(HandyInt):
    def __init__(self, integer):
        super(HermitDup, self).__init__(integer)

    def new(self, integer):
        return HermitDup(integer)

    def __getattr__(self, key):
        if key[0] == 'r' or key[0] == 'l':
            raise ValueError(f"can't use modulo on dup in '{key}'")
        return super(HermitDup, self).__getattr__(key)

    def __format__(self, format_spec):
        ret = format_spec.split('!', 2)
        if len(ret) == 2:
            if self.integer == 0: return ""
            prefix, suffix = ret
            spec = ''
        elif len(ret) == 3:
            if self.integer == 0: return ""
            #prefix, spec, suffix = ret TODO
            prefix, suffix, spec = ret
        else:
            prefix, suffix = '', ''
            spec = format_spec
        return prefix + super(HermitDup, self).__format__(spec) + suffix

import os
from pathlib import Path

# source_dir must be prefix of path. (both Path object)
# returns target path object
format_name_lookup_cache = {}
def format_name(formstr, index, rel_path, sel, source_dir, exists=lambda p: p.exists()):
    global format_name_lookup_cache
    path = source_dir / rel_path

    size = HandyInt(os.path.getsize(path)),
    # note that windows' file explorer's 'date' has more complex method of determination
    # if photo has no taken-time info, it usually is modified date (not created)
    # mod date is kept unchanged when copying & moving (to other drive)
    # https://superuser.com/a/1674290
    created  = HandyTime(datetime.fromtimestamp(os.path.getctime(path)).astimezone())
    modified = HandyTime(datetime.fromtimestamp(os.path.getmtime(path)).astimezone())
    accessed = HandyTime(datetime.fromtimestamp(os.path.getatime(path)).astimezone())

    # [:-1] to removing last '.'
    parents = list(p.name for p in path.relative_to(source_dir.parent).parents)
    hier = list(reversed(parents[:-1])) + ['']

    gen = lambda dup: Path(str(sel)) / (formstr.format(
        index = HandyInt(index),
        name = HandyString(path.stem),
        hier = HandySlice(hier, '\\'), # FIXME for unix path?
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
        # just return it (probably filename duplication error occures) FIXME
        return newpath0, 1

    # use 1 as default as there already is one file with the name.
    j = format_name_lookup_cache.get(str(newpath0), 1)

    while True: # FIXME this goes indefinitely.. should I add cap as an option??
        newpath = gen(j)
        if not exists(newpath):
            format_name_lookup_cache[str(newpath0)] = j+1
            return newpath, j
        j += 1