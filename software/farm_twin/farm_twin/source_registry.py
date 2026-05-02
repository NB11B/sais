import os
import yaml

class SourceRegistry:
    def __init__(self):
        self.sources = {}
        self._load()

    def _load(self):
        # Find docs/source_registry.yaml relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        path = os.path.join(base_dir, "docs", "source_registry.yaml")
        
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                    if data and isinstance(data, dict):
                        for src in data.get("sources", []):
                            self.sources[src["id"]] = src
            except Exception as e:
                print(f"Error loading source registry: {e}")
        else:
            print(f"Warning: Source registry not found at {path}")

    def get_source(self, source_id):
        return self.sources.get(source_id)

    def list_sources(self):
        return list(self.sources.values())

# Singleton instance
registry = SourceRegistry()
