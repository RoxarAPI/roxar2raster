#!python3

import argparse
import sys
import os
import json

import roxar2raster
from roxar2json import roxar_proxy as roxar

if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(
        description='Create raster image from RMS project.')

    PARSER.add_argument('project', type=str, nargs='+', help='RMS project path')

    if PARSER.prog == "surface2raster":
        PARSER.add_argument(
                "-e", "--encoding", type=str, help="Encoding: image, webviz_absolute or webviz_normalized"
        )
        PARSER.add_argument(
                "-n", "--name", type=str, help="Surface name."
        )
        PARSER.add_argument(
                "-c", "--category", type=str, help="Surface category."
        )
        PARSER.add_argument(
                "-l", "--clipboard", help="Use clipboard.", action="store_true"
        )
        PARSER.add_argument(
                "-m", "--margin", help="Clip 10 pixels off the surface edge.", action="store_true"
        )
        stype = "horizon"
    ARGS = PARSER.parse_args()

    image = None

    # Suppress Roxar API warnings to stdout
    sys.stdout = os.fdopen(os.dup(1), 'w')
    os.close(1)

    for path in ARGS.project:
        try:
            with roxar.Project.open(path, readonly=True) as roxar_project:
                if PARSER.prog == "structmod2raster":
                    image = roxar2raster.get_structural_model(roxar_project)
                elif PARSER.prog == "surface2raster":
                    category = ARGS.category
                    stype = "horizons"
                    if ARGS.clipboard:
                        stype = "clipboard"
                        category = None
                    if ARGS.encoding == "webviz_absolute":
                        image = roxar2raster.get_surface_absolute(
                                roxar_project, ARGS.name, category, stype, ARGS.margin)
                    elif ARGS.encoding == "webviz_normalized":
                        image = roxar2raster.get_surface_normalized(
                                roxar_project, ARGS.name, category, stype, ARGS.margin)
                    elif ARGS.encoding == "webviz_float":
                        image = roxar2raster.get_surface_webviz_float(
                                roxar_project, ARGS.name, category, stype, ARGS.margin)
                    elif ARGS.encoding == "ieee_float":
                        image = roxar2raster.get_surface_ieee_float(
                                roxar_project, ARGS.name, category, stype, ARGS.margin)
                    else:
                        image = roxar2raster.get_surface(
                                roxar_project, ARGS.name, category, stype, ARGS.margin)
        except NotImplementedError:
            print("Error: Roxar API needed.", file=sys.stderr)

    image.seek(0)
    sys.stdout.buffer.write(image.read())
