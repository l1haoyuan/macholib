from __future__ import print_function, absolute_import
import os
import sys

from macholib.util import is_platform_file
from macholib import macho_dump
from macholib import macho_standalone
from macholib import macho_methname

gCommand = None
gExecutableName = 'symbolobfuscator'

def check_file(fp, path, callback):
    if not os.path.exists(path):
        print(
            '%s: %s: No such file or directory' % (gCommand, path),
            file=sys.stderr)
        return 1

    try:
        is_plat = is_platform_file(path)

    except IOError as msg:
        print('%s: %s: %s' % (gCommand, path, msg), file=sys.stderr)
        return 1

    else:
        if is_plat:
            callback(fp, path)
    return 0


def walk_tree(callback, paths):
    err = 0

    for base in paths:
        if os.path.isdir(base):
            for root, dirs, files in os.walk(base):
                for fn in files:
                    err |= check_file(
                            sys.stdout, os.path.join(root, fn), callback)
        else:
            err |= check_file(sys.stdout, base, callback)

    return err

def methname_replace(args):
    if len(args) < 2:
        print_usage(sys.stderr)
        sys.exit(1)

    output = None
    idx = 0
    if args[idx] == "-o":
        if len(args) < 4:
            print_usage(sys.stderr)
            sys.exit(1)
        output = args[idx + 1]
        idx = idx + 2
        
    macho_methname.replace_methname(args[idx], args[idx + 1], output)


def print_usage(fp):
    print("Usage: " + gExecutableName + " [-o output_dir] macho_file methname_json", file=fp)
    # print("  python -mmacholib dump FILE ...", file=fp)
    # print("  python -mmacholib find DIR ...", file=fp)
    # print("  python -mmacholib standalone DIR ...", file=fp)
    # print("  python -mmacholib methname-replace [--swap-json] FILE NAME_JSON", file=fp)


def main():
    global gCommand
    if len(sys.argv) == 1:
        print_usage(sys.stderr)
        sys.exit(0)

    methname_replace(sys.argv[1:])

    # gCommand = sys.argv[1]

    # if gCommand == 'dump':
    #     walk_tree(macho_dump.print_file, sys.argv[2:])

    # elif gCommand == 'find':
    #     walk_tree(lambda fp, path: print(path, file=fp), sys.argv[2:])

    # elif gCommand == 'standalone':
    #     for dn in sys.argv[2:]:
    #         macho_standalone.standaloneApp(dn)

    # elif gCommand in ('help', '--help'):
    #     print_usage(sys.stdout)
    #     sys.exit(0)

    # elif gCommand == 'methname-replace':
    #     methname_replace(sys.argv[2:])

    # else:
    #     print_usage(sys.stderr)
    #     sys.exit(1)


if __name__ == "__main__":
    main()
