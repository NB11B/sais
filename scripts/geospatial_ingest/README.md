# SAIS Geospatial Ingest Pipeline

This directory contains the offline-first geospatial data ingestion pipeline (Work Package 2). It transforms standard open data (like USGS DEMs and SSURGO soil data) into the core intelligence layers required by the SAIS Farm Digital Twin.

## Purpose

SAIS Edge Nodes (i.MX 8M or ESP32) are resource-constrained and operate offline. Attempting to run heavy GIS libraries (like GDAL/rasterio) on the edge node itself is inefficient and prone to dependency issues.

This pipeline acts as a **provisioning tool**. It is designed to be run on the farmer's laptop or a local setup machine prior to deployment. It ingests raw GIS data and exports lightweight derived raster maps (Slope, Flow Accumulation, Runoff Risk), which are then loaded onto the SAIS node via USB or LAN.

## Pipeline Steps

1. **Terrain Derivation:** Reads `dem.tif` and computes `slope.tif` and `aspect.tif`.
2. **Hydrology Derivation:** Uses D8 flow routing to calculate `flow_accumulation.tif`.
3. **Soil Rasterization:** Reads `soils.geojson` and converts the `hydrologic_group` attribute into a mapped integer grid (`soils_hydrologic_group.tif`) aligned perfectly with the DEM.
4. **Intelligence Generation:** Computes a composite `runoff_risk.tif` based on high slope + highly impermeable soil.

## Setup

```bash
# It is highly recommended to use a virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

pip install -r requirements.txt
```

## Usage

1. Create an `input/` directory.
2. Place a Digital Elevation Model inside named `dem.tif`.
3. (Optional) Place a SSURGO soils GeoJSON file named `soils.geojson`.
4. Run the pipeline:

```bash
python pipeline.py --input ./input --output ./output
```

The derived intelligence layers will be written to the `output/` directory as standard GeoTIFFs, ready to be ingested by the SAIS dashboard.
