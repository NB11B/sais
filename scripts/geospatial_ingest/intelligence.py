import numpy as np
import rasterio

def compute_runoff_risk(slope_path, soil_raster_path, flow_acc_path, out_risk_path):
    """
    Compute a heuristic runoff susceptibility index based on Slope, Hydrologic Soil Group, and Flow Accumulation.
    This is not a strict hydrological model, but a heuristic risk index.
    
    Risk v2 Formula:
        risk = 0.35 * slope_norm + 0.25 * soil_impermeability_norm + 0.25 * flow_accumulation_norm + 0.15 (redistributed if cover absent)
    Since we don't have cover yet, we normalize weights:
        w_slope = 0.35 / 0.85
        w_soil  = 0.25 / 0.85
        w_flow  = 0.25 / 0.85
    """
    with rasterio.open(slope_path) as src:
        slope_array = src.read(1)
        profile = src.profile
        nodata = src.nodata
        
    with rasterio.open(soil_raster_path) as src:
        soil_array = src.read(1)
        
    with rasterio.open(flow_acc_path) as src:
        flow_acc_array = src.read(1)
        flow_nodata = src.nodata

    # Create joint nodata mask
    mask = np.zeros_like(slope_array, dtype=bool)
    if nodata is not None:
        mask |= (slope_array == nodata)
    if flow_nodata is not None:
        mask |= (flow_acc_array == flow_nodata)
        
    # Apply mask
    slope_masked = np.ma.masked_array(slope_array, mask)
    soil_masked = np.ma.masked_array(soil_array, mask)
    flow_acc_masked = np.ma.masked_array(flow_acc_array, mask)
    
    # Normalize slope (0-45 degrees main range)
    slope_norm = np.clip(slope_masked / 45.0, 0, 1)
    
    # Normalize soil (1-4 -> 0-1) where 4 is highly impermeable Type D
    soil_norm = np.clip(soil_masked / 4.0, 0, 1)
    
    # Normalize flow accumulation using log scale to handle extreme concentration
    flow_log = np.log1p(flow_acc_masked)
    max_flow_log = np.max(flow_log)
    if max_flow_log > 0:
        flow_acc_norm = flow_log / max_flow_log
    else:
        flow_acc_norm = np.zeros_like(flow_log)
    
    # Adjusted weights for MVP
    w_slope = 0.35 / 0.85
    w_soil = 0.25 / 0.85
    w_flow = 0.25 / 0.85
    
    risk = (w_slope * slope_norm + w_soil * soil_norm + w_flow * flow_acc_norm) * 100
    
    # Re-apply NoData
    if np.ma.is_masked(risk):
        risk = risk.filled(nodata if nodata is not None else -9999)
        if nodata is None:
            profile.update(nodata=-9999)

    profile.update(dtype=rasterio.float32, count=1, compress='deflate')
    
    with rasterio.open(out_risk_path, 'w', **profile) as dst:
        dst.write(risk.astype(np.float32), 1)
        
    return risk
