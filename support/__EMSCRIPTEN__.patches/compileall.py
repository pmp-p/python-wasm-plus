"""Module/script to fake byte-compile all .py files to .pyc files.
See module py_compile for details of the actual byte-compilation.
"""
import os
import sys
import importlib.util
import py_compile
import struct
import filecmp

from functools import partial
from pathlib import Path

__all__ = ["compile_dir","compile_file","compile_path"]


def compile_dir(dir, maxlevels=None, ddir=None, force=False,
                rx=None, quiet=0, legacy=False, optimize=-1, workers=1,
                invalidation_mode=None, *, stripdir=None,
                prependdir=None, limit_sl_dest=None, hardlink_dupes=False):
    return True

def compile_file(fullname, ddir=None, force=False, rx=None, quiet=0,
                 legacy=False, optimize=-1,
                 invalidation_mode=None, *, stripdir=None, prependdir=None,
                 limit_sl_dest=None, hardlink_dupes=False):
    if ddir is not None and (stripdir is not None or prependdir is not None):
        raise ValueError(("Destination dir (ddir) cannot be used "
                          "in combination with stripdir or prependdir"))

    return True

def compile_path(skip_curdir=1, maxlevels=0, force=False, quiet=0,
                 legacy=False, optimize=-1,
                 invalidation_mode=None):
    return True


def main():
    """Script main program."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Utilities to support installing Python libraries.')
    parser.add_argument('-l', action='store_const', const=0,
                        default=None, dest='maxlevels',
                        help="don't recurse into subdirectories")
    parser.add_argument('-r', type=int, dest='recursion',
                        help=('control the maximum recursion level. '
                              'if `-l` and `-r` options are specified, '
                              'then `-r` takes precedence.'))
    parser.add_argument('-f', action='store_true', dest='force',
                        help='force rebuild even if timestamps are up to date')
    parser.add_argument('-q', action='count', dest='quiet', default=0,
                        help='output only error messages; -qq will suppress '
                             'the error messages as well.')
    parser.add_argument('-b', action='store_true', dest='legacy',
                        help='use legacy (pre-PEP3147) compiled file locations')
    parser.add_argument('-d', metavar='DESTDIR',  dest='ddir', default=None,
                        help=('directory to prepend to file paths for use in '
                              'compile-time tracebacks and in runtime '
                              'tracebacks in cases where the source file is '
                              'unavailable'))
    parser.add_argument('-s', metavar='STRIPDIR',  dest='stripdir',
                        default=None,
                        help=('part of path to left-strip from path '
                              'to source file - for example buildroot. '
                              '`-d` and `-s` options cannot be '
                              'specified together.'))
    parser.add_argument('-p', metavar='PREPENDDIR',  dest='prependdir',
                        default=None,
                        help=('path to add as prefix to path '
                              'to source file - for example / to make '
                              'it absolute when some part is removed '
                              'by `-s` option. '
                              '`-d` and `-p` options cannot be '
                              'specified together.'))
    parser.add_argument('-x', metavar='REGEXP', dest='rx', default=None,
                        help=('skip files matching the regular expression; '
                              'the regexp is searched for in the full path '
                              'of each file considered for compilation'))
    parser.add_argument('-i', metavar='FILE', dest='flist',
                        help=('add all the files and directories listed in '
                              'FILE to the list considered for compilation; '
                              'if "-", names are read from stdin'))
    parser.add_argument('compile_dest', metavar='FILE|DIR', nargs='*',
                        help=('zero or more file and directory names '
                              'to compile; if no arguments given, defaults '
                              'to the equivalent of -l sys.path'))
    parser.add_argument('-j', '--workers', default=1,
                        type=int, help='Run compileall concurrently')
    invalidation_modes = [mode.name.lower().replace('_', '-')
                          for mode in py_compile.PycInvalidationMode]
    parser.add_argument('--invalidation-mode',
                        choices=sorted(invalidation_modes),
                        help=('set .pyc invalidation mode; defaults to '
                              '"checked-hash" if the SOURCE_DATE_EPOCH '
                              'environment variable is set, and '
                              '"timestamp" otherwise.'))
    parser.add_argument('-o', action='append', type=int, dest='opt_levels',
                        help=('Optimization levels to run compilation with. '
                              'Default is -1 which uses the optimization level '
                              'of the Python interpreter itself (see -O).'))
    parser.add_argument('-e', metavar='DIR', dest='limit_sl_dest',
                        help='Ignore symlinks pointing outsite of the DIR')
    parser.add_argument('--hardlink-dupes', action='store_true',
                        dest='hardlink_dupes',
                        help='Hardlink duplicated pyc files')

    args = parser.parse_args()
    compile_dests = args.compile_dest

    if args.rx:
        import re
        args.rx = re.compile(args.rx)

    if args.limit_sl_dest == "":
        args.limit_sl_dest = None

    if args.recursion is not None:
        maxlevels = args.recursion
    else:
        maxlevels = args.maxlevels

    if args.opt_levels is None:
        args.opt_levels = [-1]

    if len(args.opt_levels) == 1 and args.hardlink_dupes:
        parser.error(("Hardlinking of duplicated bytecode makes sense "
                      "only for more than one optimization level."))

    if args.ddir is not None and (
        args.stripdir is not None or args.prependdir is not None
    ):
        parser.error("-d cannot be used in combination with -s or -p")

    # if flist is provided then load it
    if args.flist:
        try:
            with (sys.stdin if args.flist=='-' else
                    open(args.flist, encoding="utf-8")) as f:
                for line in f:
                    compile_dests.append(line.strip())
        except OSError:
            if args.quiet < 2:
                print("Error reading file list {}".format(args.flist))
            return False

    if args.invalidation_mode:
        ivl_mode = args.invalidation_mode.replace('-', '_').upper()
        invalidation_mode = py_compile.PycInvalidationMode[ivl_mode]
    else:
        invalidation_mode = None

    success = True
    try:
        if compile_dests:
            for dest in compile_dests:
                if os.path.isfile(dest):
                    if not compile_file(dest, args.ddir, args.force, args.rx,
                                        args.quiet, args.legacy,
                                        invalidation_mode=invalidation_mode,
                                        stripdir=args.stripdir,
                                        prependdir=args.prependdir,
                                        optimize=args.opt_levels,
                                        limit_sl_dest=args.limit_sl_dest,
                                        hardlink_dupes=args.hardlink_dupes):
                        success = False
                else:
                    if not compile_dir(dest, maxlevels, args.ddir,
                                       args.force, args.rx, args.quiet,
                                       args.legacy, workers=args.workers,
                                       invalidation_mode=invalidation_mode,
                                       stripdir=args.stripdir,
                                       prependdir=args.prependdir,
                                       optimize=args.opt_levels,
                                       limit_sl_dest=args.limit_sl_dest,
                                       hardlink_dupes=args.hardlink_dupes):
                        success = False
            return success
        else:
            return compile_path(legacy=args.legacy, force=args.force,
                                quiet=args.quiet,
                                invalidation_mode=invalidation_mode)
    except KeyboardInterrupt:
        if args.quiet < 2:
            print("\n[interrupted]")
        return False
    return True


if __name__ == '__main__':
    exit_status = int(not main())
    sys.exit(exit_status)
