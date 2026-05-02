import os
import sys
import json
from datetime import datetime, timezone

sais_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(sais_root, 'software', 'farm_twin'))

from farm_twin.graph import FarmGraph
from farm_twin.ingest_geospatial import ingest_geospatial_manifest
from farm_twin.ingest_observation import ingest_farm_profile, ingest_sensor_observation
from farm_twin.cards import generate_water_retention_card

def seed_database():
    db_path = os.environ.get("SAIS_DB_PATH", os.path.join(sais_root, "sais.sqlite"))
    
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Removed existing database at {db_path}")
        except PermissionError:
            print(f"Warning: Could not remove {db_path} (file locked). Appending to existing DB.")
        
    print(f"Initializing database at {db_path}...")
    graph = FarmGraph(db_path)
    
    print("1. Ingesting Farm Profile...")
    profile_path = os.path.join(sais_root, "software", "farm_twin", "examples", "farm_profile.example.json")
    ingest_farm_profile(graph, profile_path)
    
    print("2. Ingesting Geospatial Manifest...")
    manifest_path = os.path.join(sais_root, "software", "farm_twin", "examples", "geospatial_manifest.example.json")
    ingest_geospatial_manifest(graph, manifest_path)
    
    print("3. Ingesting Observations...")
    obs1_path = os.path.join(sais_root, "software", "farm_twin", "examples", "observation.example.json")
    ingest_sensor_observation(graph, obs1_path)
    
    obs2 = {
        "schema": "sais.observation.v1",
        "node_id": "sensor-B",
        "farm_id": "local",
        "zone_id": "zone-a1",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "measurement_id": "soil.moisture.vwc",
        "layer": "SoilPhysics",
        "value": 0.28,
        "source": {"type": "sensor", "depth_cm": 30}
    }
    obs2_path = os.path.join(sais_root, "software", "dashboard", "temp_obs.json")
    with open(obs2_path, 'w') as f:
        json.dump(obs2, f)
    ingest_sensor_observation(graph, obs2_path)
    os.remove(obs2_path)
    
    print("4. Generating Intelligence Cards...")
    generate_water_retention_card(graph, "local", "field-a", "zone-a1")
    
    graph.storage.conn.close()
    print("Database seeding complete!")

if __name__ == "__main__":
    seed_database()
