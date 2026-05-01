import numpy as np
import rasterio
from rasterio.transform import from_origin
import os
import sys

# Add parent dir to path to import pipeline modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from terrain import calculate_slope_and_aspect, process_hydrology

def create_synthetic_dem(path):
    """
    Creates a 10x10 synthetic DEM sloping evenly from East to West.
    """
    dem = np.zeros((10, 10), dtype=np.float32)
    for i in range(10):
        dem[:, i] = 100 - i * 10  # Elevation decreases from West (x=0) to East? Wait.
        # x=0 is left (West), x=9 is right (East). So elevation decreases going East.
        # Wait, usually geographic maps: North=up, East=right. 
        # So x=0 is West, x=9 is East. If dem[:, i] = 100 - i*10, it's highest in West, lowest in East.
        # So it slopes towards the East. Aspect should be ~90 degrees.
        
    transform = from_origin(0, 100, 10, 10)  # Origin (0,100), pixel size 10x10
    
    # Use an arbitrary projected CRS (EPSG:32610 - UTM Zone 10N) for safety check
    with rasterio.open(
        path,
        'w',
        driver='GTiff',
        height=10,
        width=10,
        count=1,
        dtype=dem.dtype,
        crs='EPSG:32610',
        transform=transform,
        nodata=-9999
    ) as dst:
        dst.write(dem, 1)
        
    return dem

def test_pipeline():
    test_dir = os.path.join(os.path.dirname(__file__), 'test_output')
    os.makedirs(test_dir, exist_ok=True)
    
    dem_path = os.path.join(test_dir, 'synth_dem.tif')
    slope_path = os.path.join(test_dir, 'synth_slope.tif')
    aspect_path = os.path.join(test_dir, 'synth_aspect.tif')
    flow_acc_path = os.path.join(test_dir, 'synth_flow_acc.tif')
    
    print("Creating synthetic DEM...")
    create_synthetic_dem(dem_path)
    
    print("Calculating slope and aspect...")
    slope, aspect = calculate_slope_and_aspect(dem_path, slope_path, aspect_path)
    
    # Check slope: dz=10, dx=10 -> gradient 1.0 -> 45 degrees
    center_slope = slope[5, 5]
    print(f"Center slope: {center_slope:.2f} degrees (Expected ~45.0)")
    assert 40 < center_slope < 50, "Slope calculation is incorrect."
    
    # Check aspect: Sloping to the East (downhill towards right) means aspect ~90 degrees
    center_aspect = aspect[5, 5]
    print(f"Center aspect: {center_aspect:.2f} degrees (Expected ~90.0)")
    assert 80 < center_aspect < 100, "Aspect calculation is incorrect."
    
    print("Calculating flow accumulation...")
    acc = process_hydrology(dem_path, flow_acc_path)
    
    # Flow should accumulate from West (x=0) to East (x=9)
    # The rightmost column (x=9) should have high accumulation
    max_acc_col = np.argmax(np.sum(acc, axis=0))
    print(f"Flow accumulation concentrates at column: {max_acc_col} (Expected 9)")
    assert max_acc_col == 9, "Flow accumulation is incorrect."
    
    print("\nAll synthetic DEM tests passed successfully!")

if __name__ == "__main__":
    test_pipeline()
