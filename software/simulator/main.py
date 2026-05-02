import argparse
import time
import yaml
import os
from datetime import datetime, timezone
from client import TelemetryClient
from node import SoilMoistureNode, WeatherStationNode

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="SAIS Multi-Node Simulator")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML")
    args = parser.parse_args()

    # Find config relative to script if not absolute
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(__file__), config_path)

    config = load_config(config_path)
    farm_id = config["farm_id"]
    client = TelemetryClient(config["url"])
    interval = config.get("interval_sec", 5)

    nodes = []
    for n_cfg in config["nodes"]:
        if n_cfg["type"] == "moisture":
            nodes.append(SoilMoistureNode(
                n_cfg["id"], farm_id, n_cfg["zone_id"], 
                depth_cm=n_cfg.get("depth_cm", 30),
                drying_rate=n_cfg.get("drying_rate", 0.01)
            ))
        elif n_cfg["type"] == "weather":
            nodes.append(WeatherStationNode(n_cfg["id"], farm_id))

    print(f"🚀 Starting SAIS Multi-Node Simulator")
    print(f"Farm: {farm_id} | Target: {config['url']}")
    print(f"Nodes Active: {len(nodes)} (Interval: {interval}s)")
    print("Press Ctrl+C to exit.\n")

    try:
        while True:
            # Get current weather if any to inform soil moisture (rain events)
            current_rain = 0.0
            for node in nodes:
                if isinstance(node, WeatherStationNode):
                    node.tick()
                    for obs in node.get_observations():
                        if obs["measurement_id"] == "weather.rainfall.hourly":
                            current_rain = obs["value"]
            
            # Tick and Post all nodes
            for node in nodes:
                if isinstance(node, SoilMoistureNode):
                    if current_rain > 0:
                        print(f"🌧️ Rain event! Applying {current_rain}mm to {node.node_id}")
                        node.rain_event(current_rain)
                    node.tick()
                elif not isinstance(node, WeatherStationNode):
                    node.tick()

                for obs in node.get_observations():
                    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    
                    print(f"[{time.strftime('%H:%M:%S')}] {node.node_id} -> {obs['measurement_id']}: {obs['value']} {obs.get('unit','')}", end=" ", flush=True)
                    
                    success, result = client.post_observation(
                        node_id=node.node_id,
                        farm_id=node.farm_id,
                        zone_id=node.zone_id,
                        measurement_id=obs["measurement_id"],
                        layer=obs["layer"],
                        value=obs["value"],
                        timestamp=timestamp,
                        unit=obs.get("unit"),
                        source=obs["source"]
                    )
                    
                    if success:
                        print("✅")
                    else:
                        print(f"❌ ({result})")

            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nSimulator stopped cleanly.")

if __name__ == "__main__":
    main()
