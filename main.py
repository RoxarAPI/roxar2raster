#!python3

"Script for extracting raster formats from the RoxarAPI."

import argparse
import sys
import os

import roxar2raster
import roxar_proxy as roxar

if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(
        description="Create raster image from RMS project."
    )

    PARSER.add_argument("project", type=str, nargs="+", help="RMS project path")

    if PARSER.prog == "surface2raster":
        PARSER.add_argument(
            "-e",
            "--encoding",
            type=str,
            help="Encoding: image, webviz_absolute, webviz_normalized, npz, float32 or ieee_float_png",
        )
        PARSER.add_argument("-n", "--name", type=str, help="Surface name.")
        PARSER.add_argument(
            "-c",
            "--category",
            type=str,
            help="Surface category. If clipboard is used, this corresponds to a clipboard folder path.",
        )
        PARSER.add_argument(
            "-l", "--clipboard", help="Use clipboard.", action="store_true"
        )
        stype = "horizon"
    ARGS = PARSER.parse_args()

    image = None

    # Suppress Roxar API warnings to stdout
    sys.stdout = os.fdopen(os.dup(1), "w")
    os.close(1)

    for path in ARGS.project:
        try:
            with roxar.Project.open(path, readonly=True) as roxar_project:
                if PARSER.prog == "surface2raster":
                    category = ARGS.category
                    stype = "horizons"
                    if ARGS.clipboard:
                        stype = "clipboard"
                    if ARGS.encoding == "webviz_absolute":
                        image = roxar2raster.get_surface_absolute(
                            roxar_project, ARGS.name, category, stype
                        )
                    elif ARGS.encoding == "webviz_normalized":
                        image = roxar2raster.get_surface_normalized(
                            roxar_project, ARGS.name, category, stype
                        )
                    elif ARGS.encoding == "webviz_float":
                        image = roxar2raster.get_surface_webviz_float(
                            roxar_project, ARGS.name, category, stype
                        )
                    elif ARGS.encoding == "ieee_float_png":
                        image = roxar2raster.get_surface_ieee_float(
                            roxar_project, ARGS.name, category, stype
                        )
                    elif ARGS.encoding == "npz":
                        image = roxar2raster.get_surface_npz(
                            roxar_project, ARGS.name, category, stype
                        )
                    elif ARGS.encoding == "float32":
                        image = roxar2raster.get_surface_float32(
                            roxar_project, ARGS.name, category, stype
                        )
                    else:
                        image = roxar2raster.get_surface(
                            roxar_project, ARGS.name, category, stype
                        )
        except NotImplementedError:
            print("Error: Roxar API needed.", file=sys.stderr)

    image.seek(0)
    sys.stdout.buffer.write(image.read())
