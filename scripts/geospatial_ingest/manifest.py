import os
import json
from datetime import datetime

def generate_manifest(input_dir, output_dir):
    """
    Generate a geospatial manifest bridging this pipeline to the Farm Digital Twin.
    """
    manifest_path = os.path.join(output_dir, 'manifest.json')
    
    # We assume 'local' as a default farm_id for the MVP
    manifest = {
      "schema": "sais.geospatial_manifest.v1",
      "farm_id": "local",
      "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
      "input_layers": {
        "dem": "dem.tif",
        "soils": "soils.geojson"
      },
      "derived_layers": {
        "slope": "slope.tif",
        "aspect": "aspect.tif",
        "flow_accumulation": "flow_accumulation.tif"
      },
      "assumptions": [
        "runoff_risk is a heuristic susceptibility index",
        "combined hydrologic groups A/D, B/D, C/D treated conservatively as D",
        "risk does not yet include vegetation cover or rainfall intensity"
      ]
    }
    
    if os.path.exists(os.path.join(output_dir, 'soils_hydrologic_group.tif')):
        manifest["derived_layers"]["soils_hydrologic_group"] = "soils_hydrologic_group.tif"
        manifest["derived_layers"]["runoff_risk"] = "runoff_risk.tif"
        
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
        
    return manifest_path
