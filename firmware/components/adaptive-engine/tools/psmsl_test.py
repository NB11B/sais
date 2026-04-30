#!/usr/bin/env python3
"""
PSMSL Serial Test Tool

Host-side Python script for testing PSMSL firmware via USB serial connection.

Usage:
    python psmsl_test.py --port /dev/ttyUSB0 --test all
    python psmsl_test.py --port COM3 --monitor 100
    python psmsl_test.py --port /dev/ttyUSB0 --interactive

Requirements:
    pip install pyserial

Adaptive Crossover Firmware
Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
"""

import argparse
import json
import sys
import time
from typing import Optional, Dict, Any, List

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("Error: pyserial not installed. Run: pip install pyserial")
    sys.exit(1)


class PSMSLTester:
    """PSMSL Serial Test Interface"""
    
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 2.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None
        
    def connect(self) -> bool:
        """Connect to the ESP32 via serial port"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            # Wait for device to be ready
            time.sleep(0.5)
            # Clear any pending data
            self.serial.reset_input_buffer()
            print(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to {self.port}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from serial port"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("Disconnected")
    
    def send_command(self, cmd: str) -> List[str]:
        """Send command and read response"""
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("Not connected")
        
        # Send command
        self.serial.write((cmd + "\n").encode())
        self.serial.flush()
        
        # Read response until we see the prompt
        lines = []
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            if self.serial.in_waiting:
                line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    lines.append(line)
                    # Check for prompt
                    if line.endswith(">"):
                        break
            else:
                time.sleep(0.01)
        
        return lines
    
    def get_status(self) -> Dict[str, Any]:
        """Get current PSMSL status as dictionary"""
        lines = self.send_command("json")
        
        for line in lines:
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    pass
        
        return {}
    
    def run_test(self, test_type: str, freq: float = 1000.0) -> Dict[str, Any]:
        """Run a specific test"""
        if test_type == "sine":
            cmd = f"test sine {freq}"
        elif test_type == "sweep":
            cmd = "test sweep"
        elif test_type == "noise":
            cmd = "test noise"
        elif test_type == "room":
            cmd = "test room"
        elif test_type == "all":
            cmd = "test all"
        else:
            raise ValueError(f"Unknown test type: {test_type}")
        
        lines = self.send_command(cmd)
        
        # Parse results
        result = {
            "test_type": test_type,
            "passed": False,
            "lines": lines
        }
        
        for line in lines:
            if "PASS" in line:
                result["passed"] = True
            elif "Coherence:" in line:
                parts = line.split(",")
                for part in parts:
                    if "Coherence:" in part:
                        result["coherence"] = float(part.split(":")[1].strip())
                    elif "Curvature:" in part:
                        result["curvature"] = float(part.split(":")[1].strip())
                    elif "Residual:" in part:
                        result["residual"] = float(part.split(":")[1].strip())
        
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run full test suite"""
        print("\n" + "=" * 50)
        print("Running PSMSL Full Test Suite")
        print("=" * 50 + "\n")
        
        lines = self.send_command("test all")
        
        # Print output
        for line in lines:
            print(line)
        
        # Parse summary
        result = {
            "passed": 0,
            "total": 0,
            "lines": lines
        }
        
        for line in lines:
            if "passed" in line.lower() and "/" in line:
                parts = line.split("/")
                try:
                    result["passed"] = int(parts[0].split()[-1])
                    result["total"] = int(parts[1].split()[0])
                except (ValueError, IndexError):
                    pass
        
        return result
    
    def verify_thyme_identity(self) -> bool:
        """Verify Thyme Identity on device"""
        print("\nVerifying Thyme Identity: π² = (7φ² + √2) / 2")
        
        lines = self.send_command("thyme")
        
        for line in lines:
            print(line)
        
        # Check for success
        for line in lines:
            if "Error:" in line:
                error = float(line.split(":")[1].strip())
                return error < 1e-4
        
        return True
    
    def monitor(self, interval_ms: int = 100, duration_s: float = 10.0):
        """Monitor PSMSL output in real-time"""
        print(f"\nMonitoring PSMSL output (interval: {interval_ms}ms, duration: {duration_s}s)")
        print("Press Ctrl+C to stop\n")
        
        # Start monitoring
        self.send_command(f"monitor {interval_ms}")
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration_s:
                if self.serial.in_waiting:
                    line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                    if line and not line.endswith(">"):
                        # Try to parse as JSON
                        if line.startswith("{"):
                            try:
                                data = json.loads(line)
                                print(f"ρ={data.get('coherence', 0):.3f} "
                                      f"Ω={data.get('curvature', 0):.3f} "
                                      f"r={data.get('residual', 0):.3f} "
                                      f"E={data.get('total_energy', 0):.1f}dB")
                            except json.JSONDecodeError:
                                print(line)
                        else:
                            print(line)
                else:
                    time.sleep(0.01)
        except KeyboardInterrupt:
            print("\nStopping monitor...")
        
        # Stop monitoring
        self.send_command("stop")
    
    def interactive(self):
        """Interactive command mode"""
        print("\nInteractive mode. Type 'exit' to quit.\n")
        
        try:
            while True:
                cmd = input("psmsl> ").strip()
                
                if cmd.lower() in ["exit", "quit", "q"]:
                    break
                
                if not cmd:
                    continue
                
                lines = self.send_command(cmd)
                for line in lines:
                    if not line.endswith(">"):
                        print(line)
        except KeyboardInterrupt:
            print("\n")
        except EOFError:
            print("\n")


def list_ports():
    """List available serial ports"""
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("No serial ports found")
        return
    
    print("\nAvailable serial ports:")
    for port in ports:
        print(f"  {port.device}: {port.description}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="PSMSL Serial Test Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                          List available serial ports
  %(prog)s --port /dev/ttyUSB0 --test all  Run full test suite
  %(prog)s --port COM3 --test sine 440     Test with 440 Hz sine wave
  %(prog)s --port /dev/ttyUSB0 --monitor   Monitor output in real-time
  %(prog)s --port /dev/ttyUSB0 --thyme     Verify Thyme Identity
  %(prog)s --port /dev/ttyUSB0 -i          Interactive mode
        """
    )
    
    parser.add_argument("--list", "-l", action="store_true",
                        help="List available serial ports")
    parser.add_argument("--port", "-p", type=str,
                        help="Serial port (e.g., /dev/ttyUSB0 or COM3)")
    parser.add_argument("--baud", "-b", type=int, default=115200,
                        help="Baud rate (default: 115200)")
    parser.add_argument("--test", "-t", nargs="*",
                        help="Run test (sine [freq], sweep, noise, room, all)")
    parser.add_argument("--monitor", "-m", type=int, nargs="?", const=100,
                        help="Monitor mode with interval in ms (default: 100)")
    parser.add_argument("--duration", "-d", type=float, default=10.0,
                        help="Monitor duration in seconds (default: 10)")
    parser.add_argument("--thyme", action="store_true",
                        help="Verify Thyme Identity")
    parser.add_argument("--status", "-s", action="store_true",
                        help="Get current status")
    parser.add_argument("--json", "-j", action="store_true",
                        help="Output status as JSON")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Interactive command mode")
    
    args = parser.parse_args()
    
    # List ports
    if args.list:
        list_ports()
        return 0
    
    # Check port
    if not args.port:
        print("Error: --port is required")
        print("Use --list to see available ports")
        return 1
    
    # Create tester
    tester = PSMSLTester(args.port, args.baud)
    
    if not tester.connect():
        return 1
    
    try:
        # Run requested operation
        if args.test:
            test_type = args.test[0] if args.test else "all"
            freq = float(args.test[1]) if len(args.test) > 1 else 1000.0
            
            if test_type == "all":
                result = tester.run_all_tests()
                print(f"\nResult: {result['passed']}/{result['total']} tests passed")
            else:
                result = tester.run_test(test_type, freq)
                print(f"\nResult: {'PASS' if result['passed'] else 'FAIL'}")
                if 'coherence' in result:
                    print(f"  Coherence: {result['coherence']:.4f}")
                    print(f"  Curvature: {result['curvature']:.4f}")
                    print(f"  Residual: {result['residual']:.4f}")
        
        elif args.monitor is not None:
            tester.monitor(args.monitor, args.duration)
        
        elif args.thyme:
            success = tester.verify_thyme_identity()
            print(f"\nThyme Identity: {'VERIFIED' if success else 'FAILED'}")
        
        elif args.status:
            lines = tester.send_command("status")
            for line in lines:
                if not line.endswith(">"):
                    print(line)
        
        elif args.json:
            status = tester.get_status()
            print(json.dumps(status, indent=2))
        
        elif args.interactive:
            tester.interactive()
        
        else:
            # Default: show help
            lines = tester.send_command("help")
            for line in lines:
                if not line.endswith(">"):
                    print(line)
    
    finally:
        tester.disconnect()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
