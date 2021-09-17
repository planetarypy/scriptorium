#!/usr/bin/env python
'''Uses the SPICE mkdsk program to convert a .obj file to a .bds file.

Requires that the SPICE toolkit be installed on your system.  This
program will create a "cleaned" version of the .obj file (since a
.obj file can contain "more" than what the mkdsk program needs to
operate), it will create a mkdsksetup file that can be given to the
SPICE mkdsk program, and then it will run mkdsk for you.
'''

# Copyright 2019-2021, Ross A. Beyer (rbeyer@rossbeyer.net)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import subprocess
from pathlib import Path

# Changing "spice_path" and the values in the "defaults" dictionary for your
# particular setup will make you much happier. These are set for my MU69 setup.

# spice_path is *only* used to help set values in the "defaults" dictionary.
spice_path = Path('/Users/rbeyer/projects/new_horizons/kem_science_spice')

# This "defaults" dictionary just sets command-line argument defaults, so
# you don't have to manually type them in all the time, if you use this
# script frequently.  Read the help strings for the arguments of the same
# name to better understand them.
defaults = dict(
    surface="2486958",
    center="2486958",
    frame="MU69_FIXED",
    lsk=(spice_path / 'lsk' / 'naif0012.tls'),
    kernels=(spice_path / 'ggi' / 'nh_mu69.tpc')
)
# You may also want to consider altering the template for the mkdsksetup file
# down in the get_setup() function.


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-o', '--output',  required=False, default='.bds',
        help="The name of the output DSK file.  If this begins with a '.', "
             "it is considered a suffix and will be swapped with the input"
             "file's suffix to determine the file to write. "
             "Default: %(default)s"
    )
    parser.add_argument(
        '-s', '--surface', required=False, default=defaults["surface"],
        help="Value to be given to the SURFACE_NAME parameter in the "
             "mkdsksetup file. "
             "Default: %(default)s"
    )
    parser.add_argument(
        '-c', '--center', required=False, default=defaults["center"],
        help="Value to be given to the CENTER_NAME parameter in the "
             "mkdsksetup file. "
             "Default: %(default)s"
    )
    parser.add_argument(
        '-f', '--frame', required=False, default=defaults["frame"],
        help="Value to be given to the REF_FRAME_NAME parameter in the "
             "mkdsksetup file. "
             "Default: %(default)s"
    )
    parser.add_argument(
        '-l', '--lsk', required=False, default=defaults["lsk"],
        help="Value to be given to the LEAPSECONDS_FILE parameter in the "
             "mkdsksetup file. "
             "Default: %(default)s"

    )
    parser.add_argument(
        '--kernels', required=False, default=defaults["kernels"],
        help="Value to be given to the KERNELS_TO_LOAD parameter in the "
             "mkdsksetup file. "
             "Default: %(default)s"
    )
    parser.add_argument(
        '-k', '--keep', required=False, default=False,
        help="Keep intermediary files."
    )
    parser.add_argument(
        "-m", "--mkdsksetup", type=Path,
        help="A valid mkdesksetup file.  If given, the -s, -c, -f, -l, and -n "
             "arguments are ignored, and only the .obj cleaning, and then "
             "running of mkdsk is done (because an mkdsksetup file doesn't "
             "need to be made."
    )
    parser.add_argument(
        '-n', '--dry-run', action="store_true",
        help="Just print the contents of the mkdsksetup file that would be "
             "made."
    )
    parser.add_argument('file', help='.obj file')
    return parser


def main():
    args = arg_parser().parse_args()

    mkdsksetup = get_setup(
        args.surface, args.center, args.frame, args.lsk, args.kernels
    )

    if args.dry_run and args.mkdsksetup is None:
        print(mkdsksetup)
        return

    in_obj = Path(args.file)

    out_dsk = None
    if args.output.startswith('.'):
        out_dsk = in_obj.with_suffix(args.output)
    else:
        out_dsk = Path(args.output)

    # Step 1: clean the object file:
    cleaned_obj = in_obj.with_suffix('.obj2dsk.cleaned.obj')
    with open(in_obj, 'r') as f:
        with open(cleaned_obj, 'w') as clean:
            for line in f:
                if line.startswith('v '):
                    clean.write(line)
                elif line.startswith('f'):
                    tokens = line.split()
                    out = 'f'
                    for i in tokens[1:]:
                        v = i.split('/')[0]
                        out += ' ' + v
                    clean.write(out + '\n')

    # Step 2: make the setup file:
    if args.mkdsksetup is not None:
        setup_file = args.mkdsksetup
    else:
        setup_file = in_obj.with_suffix('.obj2dsk.mkdsksetup')
        with open(setup_file, 'w') as s:
            s.write(mkdsksetup)

    # Step 3: Run mkdsk:
    subprocess.run(['mkdsk',
                    '-setup', str(setup_file),
                    '-input', str(cleaned_obj),
                    '-output', str(out_dsk)],
                   check=True)

    # Step 4: cleanup
    if not args.keep:
        cleaned_obj.unlink()

    if not args.keep and args.mkdsksetup is None:
        setup_file.unlink()

    return


def get_setup(surfname, centername, refframe, lsk, kernels):
    return (f'''\
\\begindata

COMMENT_FILE        = ' '
SURFACE_NAME        = '{surfname}'
CENTER_NAME         = '{centername}'
REF_FRAME_NAME      = '{refframe}'
START_TIME          = '1950-JAN-1/00:00:00'
STOP_TIME           = '2050-JAN-1/00:00:00'
DATA_CLASS          = 2
INPUT_DATA_UNITS    = ( 'ANGLES    = DEGREES'
                        'DISTANCES = KILOMETERS' )
COORDINATE_SYSTEM   = 'LATITUDINAL'
MINIMUM_LATITUDE    = -90
MAXIMUM_LATITUDE    =  90
MINIMUM_LONGITUDE   = -180
MAXIMUM_LONGITUDE   =  180
DATA_TYPE           = 2
PLATE_TYPE          = 3
FINE_VOXEL_SCALE    = 4.0
COARSE_VOXEL_SCALE  = 5

LEAPSECONDS_FILE    = '{lsk}'
KERNELS_TO_LOAD = ('{kernels}' )
''')


if __name__ == "__main__":
    main()
