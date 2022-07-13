# roxar2raster
Serializes RMS project data to raster formats.

Supported formats:

- *webviz_normalized* - PNG encapsulated normalized values 
- *image* - PNG image
- *webviz_absolute* - PNG encapsulated absolute values (WebViz specific)
- *ieee_float_png* - PNG encapsulated IEEE float values
- *npz* - Compressed numpy array (NPZ)
- *float32* - Float 32 byte buffer

# Usage

Synopsis:

```
./surface2raster -h
```

Example:
```
roxenv python ./surface2raster -e webviz_normalized -l -n "hugin_depth" -c ClipboardFolder volve.pro > hugin_depth.png
```
