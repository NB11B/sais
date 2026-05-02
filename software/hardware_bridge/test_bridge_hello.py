import pytest
import socket
import time
import threading
import httpx
from software.hardware_bridge.hardware_bridge import main as bridge_main

def test_bridge_hello_parsing(monkeypatch):
    # This test verifies that the bridge correctly parses HELLO packets
    # and forwards them to the API.
    
    node_id = "bridge-test-node"
    hello_packet = f"HELLO,{node_id},1.0.0,esp32,soil|temp,4200,-60"
    
    forwarded_payloads = []
    
    class MockClient:
        def __init__(self, url):
            self.endpoint_url = url
        def post_hello(self, node_id, capabilities, rssi, battery, firmware, hardware):
            forwarded_payloads.append({
                "id": node_id,
                "capabilities": capabilities,
                "rssi": rssi,
                "battery": battery,
                "firmware": firmware,
                "hardware": hardware
            })
            return True, {"status": "success"}
        def post_observation(self, **kwargs):
            return True, {"status": "success"}

    monkeypatch.setattr("software.hardware_bridge.hardware_bridge.TelemetryClient", MockClient)
    
    # We need to run the bridge in a way that we can send a packet and then stop it.
    # Since the bridge has a 'while True' loop, we'll mock the socket to return one packet and then raise KeyboardInterrupt.
    
    class MockSocket:
        def __init__(self, *args): pass
        def bind(self, addr): pass
        def recvfrom(self, bufsize):
            # Return our packet once, then stop
            return hello_packet.encode('utf-8'), ("127.0.0.1", 12345)
        def close(self): pass

    # To break the loop after one packet, we can use a side effect or a counter
    call_count = 0
    def mock_recvfrom(self, bufsize):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return hello_packet.encode('utf-8'), ("127.0.0.1", 12345)
        raise KeyboardInterrupt()

    monkeypatch.setattr("socket.socket", MockSocket)
    monkeypatch.setattr(MockSocket, "recvfrom", mock_recvfrom)
    
    # Run the bridge main with minimal args
    monkeypatch.setattr("sys.argv", ["hardware_bridge.py", "--port", "5001"])
    
    bridge_main()
    
    # Verify the payload
    assert len(forwarded_payloads) == 1
    p = forwarded_payloads[0]
    assert p["id"] == node_id
    assert p["capabilities"] == ["soil", "temp"]
    assert p["rssi"] == -60
    assert p["battery"] == 4200
    assert p["firmware"] == "1.0.0"
    assert p["hardware"] == "esp32"
