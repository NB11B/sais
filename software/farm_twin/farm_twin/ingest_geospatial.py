import json
import os
from .graph import FarmGraph
from .models import Farm, GeospatialLayer

def ingest_geospatial_manifest(graph: FarmGraph, manifest_path: str):
    """
    Parses a WP2 geospatial manifest.json and populates the FarmGraph.
    Registers the Farm node, GeospatialLayer nodes, and maps them to Ontology layers.
    """
    with open(manifest_path, 'r') as f:
        data = json.load(f)
        
    farm_id = data.get("farm_id", "local")
    
    # Ensure Farm node exists
    existing_farm = graph.get_node(farm_id)
    if not existing_farm:
        farm_node = Farm(id=farm_id, name=f"Farm {farm_id}")
        graph.add_node(farm_node)
        
    assumptions = data.get("assumptions", [])
    
    # Ingest derived layers
    derived_layers = data.get("derived_layers", {})
    for layer_type, path in derived_layers.items():
        layer_id = f"{farm_id}:{layer_type}"
        
        layer_node = GeospatialLayer(
            id=layer_id,
            farm_id=farm_id,
            layer_type=layer_type,
            path=path,
            assumptions=assumptions
        )
        graph.add_node(layer_node)
        
        # Link to farm
        graph.add_edge(farm_id, "HAS_LAYER", layer_id)
        
        # Map to ontology
        ontology_layer = "SoilPhysics"
        if layer_type in ["flow_accumulation", "runoff_risk"]:
            ontology_layer = "WaterCycle"
        elif layer_type == "soils_hydrologic_group":
            ontology_layer = "SoilPhysics"
            
        graph.add_edge(layer_id, "INFORMS", f"ontology:{ontology_layer}")
        
    return list(derived_layers.keys())
