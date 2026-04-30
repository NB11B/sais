#!/usr/bin/env python3
"""
Convergence Logger

Real-time logging and visualization of PSMSL convergence metrics.
Captures Leibniz-Bocker diagnostics and generates reports/graphs.

Usage:
    python convergence_logger.py --port COM3 --duration 60
    python convergence_logger.py --port /dev/ttyUSB0 --live
    python convergence_logger.py --port COM3 --output session.csv --plot

Adaptive Crossover Firmware
Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
"""

import argparse
import csv
import json
import sys
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from collections import deque

try:
    import serial
except ImportError:
    print("Error: pyserial not installed. Run: pip install pyserial")
    sys.exit(1)

# Optional plotting support
try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Note: matplotlib not installed. Plotting disabled.")


@dataclass
class ConvergencePoint:
    """Single convergence measurement"""
    timestamp: float
    elapsed_s: float
    coherence: float
    curvature: float
    residual: float
    convergence: float
    stability: float
    novelty: float
    energy_db: float
    centroid_hz: float
    sectors: List[float] = field(default_factory=list)


class ConvergenceLogger:
    """Real-time convergence logging system"""
    
    SECTOR_NAMES = [
        "Foundation", "Structure", "Body", "Presence",
        "Clarity", "Air", "Extension"
    ]
    
    def __init__(self, port: str, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial: Optional[serial.Serial] = None
        
        self.data: List[ConvergencePoint] = []
        self.start_time: float = 0
        self.running = False
        self.lock = threading.Lock()
        
        # Callbacks
        self.on_data_callback = None
        self.on_converged_callback = None
        
        # Configuration
        self.poll_interval_ms = 100
        self.convergence_threshold = 0.8
        self.convergence_stable_count = 5
        
    def connect(self) -> bool:
        """Connect to ESP32"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.5
            )
            time.sleep(0.3)
            self.serial.reset_input_buffer()
            return True
        except serial.SerialException as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from ESP32"""
        self.running = False
        if self.serial and self.serial.is_open:
            self.serial.close()
    
    def _send_command(self, cmd: str) -> str:
        """Send command and get response"""
        if not self.serial:
            return ""
        
        self.serial.reset_input_buffer()
        self.serial.write((cmd + "\n").encode())
        self.serial.flush()
        
        response = ""
        start = time.time()
        
        while time.time() - start < 0.5:
            if self.serial.in_waiting:
                line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("{"):
                    return line
                response += line + "\n"
            else:
                time.sleep(0.01)
        
        return response
    
    def _parse_status(self, json_str: str) -> Optional[Dict[str, Any]]:
        """Parse JSON status response"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
    
    def _poll_once(self) -> Optional[ConvergencePoint]:
        """Poll device once and return data point"""
        response = self._send_command("diag json")
        data = self._parse_status(response)
        
        if not data:
            return None
        
        now = time.time()
        elapsed = now - self.start_time
        
        point = ConvergencePoint(
            timestamp=now,
            elapsed_s=elapsed,
            coherence=data.get("coherence", 0),
            curvature=data.get("curvature", 0),
            residual=data.get("residual", 0),
            convergence=data.get("convergence", 0),
            stability=data.get("stability", 0),
            novelty=data.get("novelty", 0),
            energy_db=data.get("energy", -100),
            centroid_hz=data.get("centroid", 0),
            sectors=data.get("sectors", [])
        )
        
        return point
    
    def _logging_thread(self, duration_s: float):
        """Background logging thread"""
        self.start_time = time.time()
        stable_count = 0
        converged = False
        
        while self.running:
            elapsed = time.time() - self.start_time
            
            if duration_s > 0 and elapsed >= duration_s:
                break
            
            point = self._poll_once()
            
            if point:
                with self.lock:
                    self.data.append(point)
                
                # Check convergence
                if point.convergence >= self.convergence_threshold:
                    stable_count += 1
                    if stable_count >= self.convergence_stable_count and not converged:
                        converged = True
                        if self.on_converged_callback:
                            self.on_converged_callback(point, elapsed)
                else:
                    stable_count = 0
                
                # Callback
                if self.on_data_callback:
                    self.on_data_callback(point)
            
            time.sleep(self.poll_interval_ms / 1000.0)
        
        self.running = False
    
    def start_logging(self, duration_s: float = 0):
        """Start logging in background thread"""
        if self.running:
            return
        
        self.data = []
        self.running = True
        
        thread = threading.Thread(
            target=self._logging_thread,
            args=(duration_s,),
            daemon=True
        )
        thread.start()
    
    def stop_logging(self):
        """Stop logging"""
        self.running = False
    
    def wait_for_completion(self, timeout_s: float = None):
        """Wait for logging to complete"""
        start = time.time()
        while self.running:
            if timeout_s and (time.time() - start) >= timeout_s:
                self.stop_logging()
                break
            time.sleep(0.1)
    
    def get_data(self) -> List[ConvergencePoint]:
        """Get logged data"""
        with self.lock:
            return list(self.data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate statistics from logged data"""
        data = self.get_data()
        
        if not data:
            return {}
        
        coherences = [p.coherence for p in data]
        curvatures = [p.curvature for p in data]
        residuals = [p.residual for p in data]
        convergences = [p.convergence for p in data]
        
        # Find convergence time
        convergence_time = None
        for p in data:
            if p.convergence >= self.convergence_threshold:
                convergence_time = p.elapsed_s
                break
        
        return {
            "duration_s": data[-1].elapsed_s if data else 0,
            "num_samples": len(data),
            "coherence": {
                "min": min(coherences),
                "max": max(coherences),
                "mean": sum(coherences) / len(coherences),
                "final": coherences[-1]
            },
            "curvature": {
                "min": min(curvatures),
                "max": max(curvatures),
                "mean": sum(curvatures) / len(curvatures),
                "final": curvatures[-1]
            },
            "residual": {
                "min": min(residuals),
                "max": max(residuals),
                "mean": sum(residuals) / len(residuals),
                "final": residuals[-1]
            },
            "convergence": {
                "min": min(convergences),
                "max": max(convergences),
                "mean": sum(convergences) / len(convergences),
                "final": convergences[-1]
            },
            "convergence_time_s": convergence_time,
            "converged": convergences[-1] >= self.convergence_threshold
        }
    
    def save_csv(self, filename: str):
        """Save data to CSV file"""
        data = self.get_data()
        
        if not data:
            print("No data to save")
            return
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            header = [
                "timestamp", "elapsed_s", "coherence", "curvature",
                "residual", "convergence", "stability", "novelty",
                "energy_db", "centroid_hz"
            ]
            header.extend([f"sector_{i}" for i in range(7)])
            writer.writerow(header)
            
            # Data
            for p in data:
                row = [
                    p.timestamp, p.elapsed_s, p.coherence, p.curvature,
                    p.residual, p.convergence, p.stability, p.novelty,
                    p.energy_db, p.centroid_hz
                ]
                row.extend(p.sectors if p.sectors else [0] * 7)
                writer.writerow(row)
        
        print(f"Saved {len(data)} samples to {filename}")
    
    def save_json(self, filename: str):
        """Save data and statistics to JSON file"""
        data = self.get_data()
        stats = self.get_statistics()
        
        output = {
            "metadata": {
                "port": self.port,
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "poll_interval_ms": self.poll_interval_ms
            },
            "statistics": stats,
            "data": [
                {
                    "elapsed_s": p.elapsed_s,
                    "coherence": p.coherence,
                    "curvature": p.curvature,
                    "residual": p.residual,
                    "convergence": p.convergence,
                    "stability": p.stability,
                    "energy_db": p.energy_db
                }
                for p in data
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Saved to {filename}")
    
    def print_summary(self):
        """Print summary of logged data"""
        stats = self.get_statistics()
        
        if not stats:
            print("No data logged")
            return
        
        print("\n" + "=" * 50)
        print("CONVERGENCE LOG SUMMARY")
        print("=" * 50)
        print(f"Duration: {stats['duration_s']:.1f} seconds")
        print(f"Samples: {stats['num_samples']}")
        print()
        print("Leibniz-Bocker Diagnostics:")
        print(f"  Coherence (ρ):  {stats['coherence']['final']:.4f} "
              f"(range: {stats['coherence']['min']:.3f} - {stats['coherence']['max']:.3f})")
        print(f"  Curvature (Ω):  {stats['curvature']['final']:.4f} "
              f"(range: {stats['curvature']['min']:.3f} - {stats['curvature']['max']:.3f})")
        print(f"  Residual (r):   {stats['residual']['final']:.4f} "
              f"(range: {stats['residual']['min']:.3f} - {stats['residual']['max']:.3f})")
        print()
        print(f"Final Convergence: {stats['convergence']['final']:.1%}")
        
        if stats['convergence_time_s']:
            print(f"Time to Converge: {stats['convergence_time_s']:.1f} seconds")
        else:
            print("Time to Converge: Did not reach threshold")
        
        print(f"Status: {'CONVERGED' if stats['converged'] else 'NOT CONVERGED'}")
        print("=" * 50)


class LivePlotter:
    """Real-time plotting of convergence data"""
    
    def __init__(self, logger: ConvergenceLogger, window_size: int = 100):
        self.logger = logger
        self.window_size = window_size
        
        # Data buffers
        self.times = deque(maxlen=window_size)
        self.coherence = deque(maxlen=window_size)
        self.curvature = deque(maxlen=window_size)
        self.residual = deque(maxlen=window_size)
        self.convergence = deque(maxlen=window_size)
        
        # Setup plot
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.suptitle('PSMSL Convergence Monitor', fontsize=14)
        
        # Coherence plot
        self.ax_coh = self.axes[0, 0]
        self.ax_coh.set_title('Coherence (ρ)')
        self.ax_coh.set_ylim(0, 1)
        self.ax_coh.axhline(y=0.8, color='g', linestyle='--', alpha=0.5)
        self.line_coh, = self.ax_coh.plot([], [], 'b-', linewidth=2)
        
        # Curvature plot
        self.ax_cur = self.axes[0, 1]
        self.ax_cur.set_title('Curvature (Ω)')
        self.ax_cur.set_ylim(0, 0.5)
        self.ax_cur.axhline(y=0.2, color='g', linestyle='--', alpha=0.5)
        self.line_cur, = self.ax_cur.plot([], [], 'r-', linewidth=2)
        
        # Residual plot
        self.ax_res = self.axes[1, 0]
        self.ax_res.set_title('Residual (r)')
        self.ax_res.set_ylim(0, 1)
        self.ax_res.axhline(y=0.3, color='g', linestyle='--', alpha=0.5)
        self.line_res, = self.ax_res.plot([], [], 'm-', linewidth=2)
        
        # Convergence plot
        self.ax_conv = self.axes[1, 1]
        self.ax_conv.set_title('Convergence')
        self.ax_conv.set_ylim(0, 1)
        self.ax_conv.axhline(y=0.8, color='g', linestyle='--', alpha=0.5, label='Target')
        self.line_conv, = self.ax_conv.plot([], [], 'g-', linewidth=2)
        self.ax_conv.legend()
        
        for ax in self.axes.flat:
            ax.set_xlabel('Time (s)')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
    
    def update(self, frame):
        """Animation update function"""
        data = self.logger.get_data()
        
        if not data:
            return self.line_coh, self.line_cur, self.line_res, self.line_conv
        
        # Get recent data
        recent = data[-self.window_size:]
        
        times = [p.elapsed_s for p in recent]
        
        # Update coherence
        self.line_coh.set_data(times, [p.coherence for p in recent])
        self.ax_coh.set_xlim(min(times), max(times) + 0.1)
        
        # Update curvature
        self.line_cur.set_data(times, [p.curvature for p in recent])
        self.ax_cur.set_xlim(min(times), max(times) + 0.1)
        
        # Update residual
        self.line_res.set_data(times, [p.residual for p in recent])
        self.ax_res.set_xlim(min(times), max(times) + 0.1)
        
        # Update convergence
        self.line_conv.set_data(times, [p.convergence for p in recent])
        self.ax_conv.set_xlim(min(times), max(times) + 0.1)
        
        # Update title with current values
        if recent:
            p = recent[-1]
            self.fig.suptitle(
                f'PSMSL Convergence Monitor | '
                f'ρ={p.coherence:.3f} Ω={p.curvature:.3f} r={p.residual:.3f} '
                f'Conv={p.convergence:.1%}',
                fontsize=12
            )
        
        return self.line_coh, self.line_cur, self.line_res, self.line_conv
    
    def run(self):
        """Start live plotting"""
        ani = animation.FuncAnimation(
            self.fig, self.update, interval=100, blit=True
        )
        plt.show()


def static_plot(data: List[ConvergencePoint], output_file: str = None):
    """Generate static plot from logged data"""
    if not HAS_MATPLOTLIB:
        print("matplotlib not available for plotting")
        return
    
    times = [p.elapsed_s for p in data]
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('PSMSL Convergence Analysis', fontsize=14)
    
    # Coherence
    ax = axes[0, 0]
    ax.plot(times, [p.coherence for p in data], 'b-', linewidth=1.5, label='Coherence')
    ax.axhline(y=0.8, color='g', linestyle='--', alpha=0.5, label='Target')
    ax.set_title('Coherence (ρ)')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Coherence')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Curvature
    ax = axes[0, 1]
    ax.plot(times, [p.curvature for p in data], 'r-', linewidth=1.5)
    ax.axhline(y=0.2, color='g', linestyle='--', alpha=0.5)
    ax.set_title('Curvature (Ω)')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Curvature')
    ax.set_ylim(0, max(0.5, max(p.curvature for p in data) * 1.1))
    ax.grid(True, alpha=0.3)
    
    # Residual
    ax = axes[1, 0]
    ax.plot(times, [p.residual for p in data], 'm-', linewidth=1.5)
    ax.axhline(y=0.3, color='g', linestyle='--', alpha=0.5)
    ax.set_title('Residual (r)')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Residual')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    
    # Convergence
    ax = axes[1, 1]
    ax.fill_between(times, [p.convergence for p in data], alpha=0.3, color='green')
    ax.plot(times, [p.convergence for p in data], 'g-', linewidth=2)
    ax.axhline(y=0.8, color='orange', linestyle='--', linewidth=2, label='Threshold')
    ax.set_title('Convergence')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Convergence')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Plot saved to {output_file}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="PSMSL Convergence Logger",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--port", "-p", required=True,
                        help="Serial port (e.g., COM3 or /dev/ttyUSB0)")
    parser.add_argument("--duration", "-d", type=float, default=60,
                        help="Logging duration in seconds (0 for indefinite)")
    parser.add_argument("--interval", "-i", type=int, default=100,
                        help="Poll interval in milliseconds")
    parser.add_argument("--output", "-o", type=str,
                        help="Output CSV file")
    parser.add_argument("--json", "-j", type=str,
                        help="Output JSON file")
    parser.add_argument("--plot", action="store_true",
                        help="Generate plot after logging")
    parser.add_argument("--plot-file", type=str,
                        help="Save plot to file instead of displaying")
    parser.add_argument("--live", "-l", action="store_true",
                        help="Live plotting mode")
    parser.add_argument("--threshold", "-t", type=float, default=0.8,
                        help="Convergence threshold (default: 0.8)")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress real-time output")
    
    args = parser.parse_args()
    
    # Create logger
    logger = ConvergenceLogger(args.port)
    logger.poll_interval_ms = args.interval
    logger.convergence_threshold = args.threshold
    
    # Setup callbacks
    if not args.quiet:
        def on_data(point):
            print(f"\r[{point.elapsed_s:6.1f}s] "
                  f"ρ={point.coherence:.3f} "
                  f"Ω={point.curvature:.3f} "
                  f"r={point.residual:.3f} "
                  f"Conv={point.convergence:.1%}  ", end="")
        
        def on_converged(point, elapsed):
            print(f"\n*** CONVERGED at {elapsed:.1f}s (ρ={point.coherence:.3f}) ***")
        
        logger.on_data_callback = on_data
        logger.on_converged_callback = on_converged
    
    # Connect
    if not logger.connect():
        return 1
    
    try:
        print(f"Starting convergence logging...")
        print(f"Duration: {args.duration}s, Interval: {args.interval}ms")
        print(f"Convergence threshold: {args.threshold:.0%}")
        print("-" * 60)
        
        if args.live and HAS_MATPLOTLIB:
            # Live plotting mode
            logger.start_logging(duration_s=0)  # Indefinite
            plotter = LivePlotter(logger)
            plotter.run()
        else:
            # Standard logging mode
            logger.start_logging(duration_s=args.duration)
            logger.wait_for_completion()
        
        print("\n")
        
        # Print summary
        logger.print_summary()
        
        # Save data
        if args.output:
            logger.save_csv(args.output)
        
        if args.json:
            logger.save_json(args.json)
        
        # Generate plot
        if args.plot or args.plot_file:
            data = logger.get_data()
            if data:
                static_plot(data, args.plot_file)
            else:
                print("No data for plotting")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nLogging interrupted by user")
        logger.stop_logging()
        logger.print_summary()
        return 0
        
    finally:
        logger.disconnect()


if __name__ == "__main__":
    sys.exit(main())
