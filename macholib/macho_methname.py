import sys
import os
import json
from enum import Enum

from .mach_o import LC_SYMTAB
from macholib import MachO
from macholib import mach_o
from shutil import copy2
from shutil import SameFileError


class ReplaceType(Enum):
    objc_methname = 1
    symbol_table = 2

def replace_in_bytes(method_bytes, name_dict, type):
    is_prefix = False
    empty_byte = b'\x00'
    if not method_bytes.startswith(empty_byte):
        is_prefix = True
        method_bytes = empty_byte + method_bytes

    for key, value in name_dict.items():
        if len(key) != len(value):
            raise("replace method name with different length may break the mach-o file, ori: " +
                  key + ", dst: " + value)
        if type == ReplaceType.objc_methname:
            method_bytes = method_bytes.replace(
                empty_byte + key.encode('utf-8') + empty_byte, empty_byte + value.encode('utf-8') + empty_byte)
        elif type == ReplaceType.symbol_table:
            method_bytes = method_bytes.replace(
                b' ' + key.encode('utf-8') + b']', b' ' + value.encode('utf-8') + b']')

    if is_prefix:
        method_bytes = method_bytes.replace(empty_byte, b'', 1)
    return method_bytes


def ch_methname_sect(header, name_dict):
    commands = header.commands
    lc = None
    sect = None
    for _, command_tuple in enumerate(commands):
        seg = command_tuple[1]
        data = command_tuple[2]
        if hasattr(seg, 'segname') and seg.segname.rstrip(b'\x00') == b'__TEXT':
            for tmp_sect in data:
                if tmp_sect.sectname.rstrip(b'\x00') == b'__objc_methname':
                    lc = command_tuple[0]
                    sect = tmp_sect

    if sect is None:
        raise("Can't find __objc_methname section")
    
    sect.section_data = replace_in_bytes(
        sect.section_data, name_dict, ReplaceType.objc_methname)
    header.mod_dict[lc] = [sect]


def ch_symtab(header, name_dict):
    commands = header.commands
    for idx, command_tuple in enumerate(commands):
        lc = command_tuple[0]
        cmd = command_tuple[1]
        data = command_tuple[2]
        if lc.cmd == LC_SYMTAB:
            data = replace_in_bytes(data, name_dict, ReplaceType.symbol_table)
            header.mod_dict[lc] = [data]
            commands[idx] = (lc, cmd, data)
            return

    raise("Can't find LC_SYMTAB")

def replace_methname(macho_file, methname_json, output_dir):
    """
    Map method names in Mach-O file with the JSON file
    """

    if not os.path.isfile(macho_file):
        raise("passing not exist file " + macho_file)
    if not os.path.isfile(methname_json):
        raise("passing not exist file " + methname_json)
    if output_dir is not None and not os.path.isdir(output_dir):
        raise("passing not exist dir " + output_dir)

    macho = MachO.MachO(macho_file)

    name_dict = None
    with open(methname_json) as json_file:
        name_dict = json.load(json_file)

    for header in macho.headers:
        ch_methname_sect(header, name_dict)
        ch_symtab(header, name_dict)

    ori_dir, filename = os.path.split(macho_file)
    if output_dir is None:
        output_dir = ori_dir
    output = os.path.join(output_dir, filename)
    
    try:
        copy2(macho_file, output_dir)
    except SameFileError:
        pass

    with open(output, 'r+b') as fp:
        macho.write(fp)
    os.chmod(output, 0o755)

def main():
    replace_methname(sys.argv[0], sys.argv[1], sys.argv[2])


if __name__ == '__main__':
    main()
