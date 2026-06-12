"""Compile backend/locale/**/django.po into .mo files without GNU gettext.

Django's `compilemessages` needs msgfmt, which isn't always installed
(notably on Windows). This is a minimal pure-Python replacement that
handles the plain msgid/msgstr entries we use (no plural forms).

Usage:  python scripts/compile_messages.py
"""
import ast
import array
import struct
import sys
from pathlib import Path

LOCALE_DIR = Path(__file__).resolve().parent.parent / 'locale'


def parse_po(path):
    catalog = {}
    msgid = None
    msgstr = None
    mode = None

    def flush():
        if msgid is not None and msgstr:
            catalog[msgid] = msgstr

    with open(path, encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('msgid '):
                flush()
                msgid = ast.literal_eval(line[6:])
                msgstr = None
                mode = 'id'
            elif line.startswith('msgstr '):
                msgstr = ast.literal_eval(line[7:])
                mode = 'str'
            elif line.startswith('"'):
                if mode == 'id':
                    msgid += ast.literal_eval(line)
                elif mode == 'str':
                    msgstr += ast.literal_eval(line)
    flush()
    return catalog


def write_mo(catalog, path):
    keys = sorted(catalog)
    offsets = []
    ids = b''
    strs = b''
    for key in keys:
        kb = key.encode('utf-8')
        vb = catalog[key].encode('utf-8')
        offsets.append((len(ids), len(kb), len(strs), len(vb)))
        ids += kb + b'\x00'
        strs += vb + b'\x00'

    n = len(keys)
    keystart = 7 * 4 + 16 * n
    valuestart = keystart + len(ids)
    koffsets = []
    voffsets = []
    for o1, l1, o2, l2 in offsets:
        koffsets += [l1, o1 + keystart]
        voffsets += [l2, o2 + valuestart]

    output = struct.pack('Iiiiiii',
                         0x950412DE,        # magic
                         0,                 # version
                         n,                 # number of entries
                         7 * 4,             # start of key index
                         7 * 4 + n * 8,     # start of value index
                         0, 0)              # size/offset of hash table (unused)
    output += array.array('i', koffsets + voffsets).tobytes()
    output += ids + strs
    with open(path, 'wb') as f:
        f.write(output)


def main():
    po_files = sorted(LOCALE_DIR.glob('*/LC_MESSAGES/*.po'))
    if not po_files:
        print(f'no .po files found under {LOCALE_DIR}')
        sys.exit(1)
    for po in po_files:
        catalog = parse_po(po)
        mo = po.with_suffix('.mo')
        write_mo(catalog, mo)
        print(f'{po.relative_to(LOCALE_DIR.parent)} -> {mo.name} ({len(catalog) - 1} strings)')


if __name__ == '__main__':
    main()
