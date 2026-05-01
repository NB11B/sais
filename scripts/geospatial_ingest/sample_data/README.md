# Sample Data

This directory is intended for storing test data to validate the geospatial ingest pipeline. 

To run a full test, you will need:

1. **`dem.tif`**: A Digital Elevation Model (GeoTIFF) in a **projected** Coordinate Reference System (e.g., UTM in meters). Geographic CRSs (e.g., WGS84 in degrees) will be rejected by the pipeline to prevent inaccurate slope calculations.
2. **`soils.geojson`**: A vector file containing soil map units (e.g., from the USDA SSURGO database). It must contain a `hydrologic_group` attribute (or you must update the pipeline's attribute mapping in `soils.py`).

Once populated, run:
```bash
python ../pipeline.py --input . --output ../output
```
