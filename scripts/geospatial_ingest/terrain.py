import numpy as np
import rasterio
from pysheds.grid import Grid
import os
import warnings

# Suppress verbose rasterio/pysheds warnings for MVP
warnings.filterwarnings('ignore')

def calculate_slope_and_aspect(dem_path, out_slope_path, out_aspect_path):
    """
    Calculate slope and aspect in degrees from a DEM GeoTIFF.
    """
    with rasterio.open(dem_path) as src:
        dem = src.read(1)
        transform = src.transform
        cell_size_x = abs(transform[0])
        cell_size_y = abs(transform[4])
        profile = src.profile

    # Simple 2D gradient for slope/aspect
    y, x = np.gradient(dem, cell_size_y, cell_size_x)
    
    slope = np.arctan(np.sqrt(x*x + y*y)) * 180 / np.pi
    
    aspect = np.arctan2(-x, y) * 180 / np.pi
    aspect = np.where(aspect < 0, aspect + 360, aspect)

    # Write Slope
    profile.update(dtype=rasterio.float32, count=1, compress='deflate')
    with rasterio.open(out_slope_path, 'w', **profile) as dst:
        dst.write(slope.astype(np.float32), 1)

    # Write Aspect
    with rasterio.open(out_aspect_path, 'w', **profile) as dst:
        dst.write(aspect.astype(np.float32), 1)
        
    return slope, aspect

def process_hydrology(dem_path, out_flow_acc_path):
    """
    Use pysheds to calculate flow direction and accumulation.
    """
    grid = Grid.from_raster(dem_path)
    dem = grid.read_raster(dem_path)
    
    # Condition DEM (fill pits and depressions)
    pit_filled_dem = grid.fill_pits(dem)
    flooded_dem = grid.fill_depressions(pit_filled_dem)
    inflated_dem = grid.resolve_flats(flooded_dem)

    # Compute flow direction (D8)
    dirmap = (64, 128, 1, 2, 4, 8, 16, 32)
    fdir = grid.flowdir(inflated_dem, dirmap=dirmap)
    
    # Compute flow accumulation
    acc = grid.accumulation(fdir, dirmap=dirmap)
    
    # Write Flow Accumulation
    grid.to_raster(acc, out_flow_acc_path)
    
    return acc
