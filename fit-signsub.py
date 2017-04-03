#!/usr/bin/env python

import os
import argparse
import StringIO
import tempfile
import sys

from distutils import spawn

from pyfdt import pyfdt

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Example sign')
    parser.add_argument('filename',
        help="Input subordinate certificate store (DTB)")
    parser.add_argument('output',
        help="Output signed subordinate store (DTB)")
    parser.add_argument('--keydir', required=True, metavar="DIR",
        help="Required path to directory containing '.key' private key")
    parser.add_argument('--mkimage', required=True, metavar="PATH",
        help="Required path to mkimage")
    args = parser.parse_args()

    if not os.path.isdir(args.keydir):
        print("The --keydir must be a directory containing a '.key' key.")
        sys.exit(1)
    keyfile = os.path.join(args.keydir, os.path.basename(args.keydir) + ".key")
    if not os.path.exists(keyfile):
        print("Cannot find private key: %s" % (keyfile))
        sys.exit(1)

    with open(args.filename, 'rb') as fh:
        subordinate = fh.read()
        fit_io = StringIO.StringIO(subordinate)
        dtb = pyfdt.FdtBlobParse(fit_io)
        fdt = dtb.to_fdt()

    sub_image = fdt.resolve_path('/images/fdt@1/signature@1/key-name-hint')
    if sub_image is None:
        print("This subordinate store does not contain a signature node")
        sys.exit(1)
    requested_key_name = os.path.basename(args.keydir)
    sub_image.strings = [requested_key_name]
    
    subordinate_source = fdt.to_dts()
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(subordinate_source)
        tmp.flush()

        print(" ".join(
            [args.mkimage, "-f", tmp.name, "-k", args.keydir, "-r", args.output]))
        spawn.spawn(
            [args.mkimage, "-f", tmp.name, "-k", args.keydir, "-r", args.output])

    print("Wrote signed subordinate certificate store: %s" % (args.output))
