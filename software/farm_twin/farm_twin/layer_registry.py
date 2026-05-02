import os
import yaml

class LayerRegistry:
    def __init__(self):
        self.layers = {}
        self._load()

    def _load(self):
        # Find docs/layer_registry.yaml relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        path = os.path.join(base_dir, "docs", "layer_registry.yaml")
        
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                    if data and isinstance(data, dict):
                        for layer in data.get("layers", []):
                            self.layers[layer["id"]] = layer
            except Exception as e:
                print(f"Error loading layer registry: {e}")
        else:
            print(f"Warning: Layer registry not found at {path}")

    def get_layer(self, layer_id):
        return self.layers.get(layer_id)

    def list_layers(self):
        return list(self.layers.values())

# Singleton instance
registry = LayerRegistry()
