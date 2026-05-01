import numpy as np
import rasterio

def compute_runoff_risk(slope_path, soil_raster_path, out_risk_path):
    """
    Compute a simple runoff risk index based on Slope and Hydrologic Soil Group.
    High Slope + Type D Soil (4) = High Risk.
    """
    with rasterio.open(slope_path) as src:
        slope_array = src.read(1)
        profile = src.profile
        
    with rasterio.open(soil_raster_path) as src:
        soil_array = src.read(1)
        
    # Normalize slope (assuming 0-45 degrees is the main range of interest)
    # Slope > 45 is capped at 1.0 (maximum contribution)
    slope_norm = np.clip(slope_array / 45.0, 0, 1)
    
    # Normalize soil (1-4, where 4 is highly impermeable Type D)
    soil_norm = np.clip(soil_array / 4.0, 0, 1)
    
    # Simple weighted risk model: 60% driven by slope, 40% driven by soil impermeability
    # Scaled to a 0-100 index for the dashboard
    risk = (0.6 * slope_norm + 0.4 * soil_norm) * 100
    
    profile.update(dtype=rasterio.float32, count=1, compress='deflate')
    
    with rasterio.open(out_risk_path, 'w', **profile) as dst:
        dst.write(risk.astype(np.float32), 1)
        
    return risk
