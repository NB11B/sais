import socket
import argparse
import json
import sys
import os

# Add simulator to path to reuse TelemetryClient
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "simulator"))
from client import TelemetryClient

def main():
    parser = argparse.ArgumentParser(description="SAIS Live Hardware Bridge")
    parser.add_argument("--url", default="http://localhost:8000/api/observations", help="Dashboard POST URL")
    parser.add_argument("--port", type=int, default=5001, help="UDP listen port")
    parser.add_argument("--farm", default="local", help="Farm ID")
    args = parser.parse_args()

    client = TelemetryClient(args.url)
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", args.port))

    print(f"📡 SAIS Hardware Bridge Active")
    print(f"Listening on UDP :{args.port}")
    print(f"Forwarding to: {args.url}")
    print("Format expected: node_id,measurement_id,value,unit,layer")
    print("Press Ctrl+C to exit.\n")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            message = data.decode('utf-8').strip()
            print(f"[{addr[0]}] Received: {message}")
            
            parts = message.split(",")
            if len(parts) < 3:
                print(f"⚠️ Malformed message from {addr[0]}")
                continue
                
            node_id = parts[0]
            meas_id = parts[1]
            try:
                value = float(parts[2])
            except ValueError:
                print(f"⚠️ Non-numeric value in message from {addr[0]}")
                continue
                
            unit = parts[3] if len(parts) > 3 else None
            layer = parts[4] if len(parts) > 4 else "Hardware"
            
            # Post to SAIS
            success, result = client.post_observation(
                node_id=node_id,
                farm_id=args.farm,
                measurement_id=meas_id,
                layer=layer,
                value=value,
                unit=unit,
                source={"type": "hardware_bridge", "ip": addr[0]}
            )
            
            if success:
                print(f"✅ Forwarded {node_id} -> {meas_id}")
            else:
                print(f"❌ Failed to forward: {result}")
                
    except KeyboardInterrupt:
        print("\nBridge stopped cleanly.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
