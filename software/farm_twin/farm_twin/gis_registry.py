import os
import yaml
import json

class GisRegistry:
    def __init__(self):
        self.assets = {}
        self._load()

    def _load(self):
        # Find project root (assume this is in software/farm_twin/farm_twin/)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        path = os.path.join(base_dir, "docs", "gis_assets.yaml")
        
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                    if data and isinstance(data, dict):
                        for asset in data.get("assets", []):
                            # Resolve path relative to project root
                            asset["full_path"] = os.path.join(base_dir, asset["path"])
                            self.assets[asset["id"]] = asset
            except Exception as e:
                print(f"Error loading GIS registry: {e}")
        else:
            print(f"Warning: GIS registry not found at {path}")

    def get_asset_list(self):
        return [
            {k: v for k, v in asset.items() if k != "full_path"}
            for asset in self.assets.values()
        ]

    def get_asset_data(self, asset_id: str):
        asset = self.assets.get(asset_id)
        if not asset or not os.path.exists(asset["full_path"]):
            return None
            
        try:
            with open(asset["full_path"], 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading GIS data for {asset_id}: {e}")
            return None
