import geopandas as gpd
import rasterio
from rasterio import features
import numpy as np
import warnings

warnings.filterwarnings('ignore')

def rasterize_soils(soils_geojson_path, template_raster_path, out_soil_raster_path, target_attribute="hydrologic_group"):
    """
    Rasterize a soil GeoJSON file using a DEM as a grid template.
    Maps hydrologic soil groups (A, B, C, D) to integers for processing.
    """
    # Read the template DEM to get dimensions and transform
    with rasterio.open(template_raster_path) as src:
        profile = src.profile
        transform = src.transform
        shape = src.shape

    # Read soils data
    gdf = gpd.read_file(soils_geojson_path)
    
    # Ensure CRS matches
    if gdf.crs != profile['crs']:
        gdf = gdf.to_crs(profile['crs'])
        
    # Map categorical hydrologic groups to integers for MVP (A=1, B=2, C=3, D=4)
    # A = High infiltration, low runoff
    # D = Low infiltration, high runoff
    mapping = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'A/D': 4, 'B/D': 4, 'C/D': 4}
    
    if target_attribute in gdf.columns:
        gdf['raster_val'] = gdf[target_attribute].map(mapping).fillna(0).astype(int)
    else:
        # Default to a moderate value if the column is missing
        gdf['raster_val'] = 2
        
    shapes = ((geom, value) for geom, value in zip(gdf.geometry, gdf['raster_val']))

    rasterized = features.rasterize(
        shapes=shapes,
        out_shape=shape,
        transform=transform,
        fill=0,
        dtype=rasterio.uint8
    )

    profile.update(dtype=rasterio.uint8, count=1, compress='deflate', nodata=0)
    
    with rasterio.open(out_soil_raster_path, 'w', **profile) as dst:
        dst.write(rasterized, 1)
        
    return rasterized
