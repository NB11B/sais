import os
import argparse
from terrain import calculate_slope_and_aspect, process_hydrology
from soils import rasterize_soils
from intelligence import compute_runoff_risk
from manifest import generate_manifest

def run_pipeline(input_dir, output_dir):
    """
    Orchestrates the offline geospatial ingest pipeline.
    Reads base layers from input_dir and generates intelligence maps in output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    dem_path = os.path.join(input_dir, 'dem.tif')
    soils_path = os.path.join(input_dir, 'soils.geojson')
    
    if not os.path.exists(dem_path):
        print(f"Error: Missing required input {dem_path}")
        print("Please provide a DEM GeoTIFF named 'dem.tif' in the input directory.")
        return
        
    print("1. Processing Terrain (Slope & Aspect)...")
    slope_path = os.path.join(output_dir, 'slope.tif')
    aspect_path = os.path.join(output_dir, 'aspect.tif')
    calculate_slope_and_aspect(dem_path, slope_path, aspect_path)
    
    print("2. Processing Hydrology (Flow Accumulation)...")
    flow_acc_path = os.path.join(output_dir, 'flow_accumulation.tif')
    process_hydrology(dem_path, flow_acc_path)
    
    soil_raster_path = None
    if os.path.exists(soils_path):
        print("3. Processing Soils (Rasterization)...")
        soil_raster_path = os.path.join(output_dir, 'soils_hydrologic_group.tif')
        rasterize_soils(soils_path, dem_path, soil_raster_path)
    
        print("4. Generating Derived Intelligence (Runoff Risk v2)...")
        risk_path = os.path.join(output_dir, 'runoff_risk.tif')
        compute_runoff_risk(slope_path, soil_raster_path, flow_acc_path, risk_path)
    else:
        print("Skipping Soils and Runoff Risk (soils.geojson not found).")
        
    print("5. Generating Manifest...")
    manifest_path = generate_manifest(input_dir, output_dir)
        
    print(f"Pipeline Complete! Derived intelligence maps saved to {output_dir}/")
    print(f"Manifest created at: {manifest_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SAIS Geospatial Ingest Pipeline")
    parser.add_argument('--input', type=str, default='input', help='Input directory containing dem.tif and soils.geojson')
    parser.add_argument('--output', type=str, default='output', help='Output directory for derived intelligence layers')
    args = parser.parse_args()
    
    run_pipeline(args.input, args.output)
