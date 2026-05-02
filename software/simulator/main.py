import argparse
import time
from client import TelemetryClient
from node import SimulatedNode

def main():
    parser = argparse.ArgumentParser(description="SAIS Sensor Node Simulator")
    parser.add_argument("--url", default="http://localhost:8000/api/observations", help="Dashboard POST URL")
    parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds")
    parser.add_argument("--farm", default="local", help="Farm ID")
    parser.add_argument("--zone", default="zone-a1", help="Zone ID")
    args = parser.parse_args()

    client = TelemetryClient(args.url)
    
    # Start at a healthy 35% moisture
    node = SimulatedNode("sim-sensor-1", args.farm, args.zone, initial_moisture=0.35)

    print(f"Starting SAIS Simulator for node '{node.node_id}' in zone '{node.zone_id}'")
    print(f"Targeting: {args.url} (Interval: {args.interval}s)")
    print("Press Ctrl+C to exit.")

    try:
        while True:
            # Automatic rain event if things get too dry
            if node.moisture < 0.15:
                print("\n--- 🌧️ AUTOMATIC RAIN EVENT TRIGGERED 🌧️ ---")
                node.rain_event()
                
            node.tick()
            obs = node.get_observation()
            
            print(f"[{time.strftime('%H:%M:%S')}] Post moisture: {obs['value']:.3f} ...", end=" ", flush=True)
            
            success, result = client.post_observation(
                node_id=node.node_id,
                farm_id=node.farm_id,
                zone_id=node.zone_id,
                measurement_id=obs["measurement_id"],
                layer=obs["layer"],
                value=obs["value"],
                source=obs["source"]
            )
            
            if success:
                print("OK")
            else:
                print(f"FAIL ({result})")
                
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\nSimulator stopped cleanly.")

if __name__ == "__main__":
    main()
