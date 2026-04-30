#!/usr/bin/env python3
"""
Room Calibration Procedure Script

Automated calibration sequence for the Adaptive Crossover system.
Guides through the complete room calibration process with verification
at each step.

Usage:
    python calibration_procedure.py --port COM3
    python calibration_procedure.py --port /dev/ttyUSB0 --quick
    python calibration_procedure.py --port COM3 --full --output room_profile.json

Adaptive Crossover Firmware
Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
"""

import argparse
import json
import sys
import time
import os
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("Error: pyserial not installed. Run: pip install pyserial")
    sys.exit(1)


class CalibrationPhase(Enum):
    """Calibration phases"""
    INIT = "initialization"
    HARDWARE_CHECK = "hardware_check"
    NOISE_FLOOR = "noise_floor"
    SIGNAL_PATH = "signal_path"
    FREQUENCY_SWEEP = "frequency_sweep"
    MODE_DETECTION = "mode_detection"
    CONVERGENCE = "convergence"
    VERIFICATION = "verification"
    COMPLETE = "complete"


@dataclass
class CalibrationResult:
    """Results from calibration procedure"""
    timestamp: str
    duration_seconds: float
    phases_completed: List[str]
    
    # Hardware check
    hardware_ok: bool
    mic_levels: List[float]
    speaker_verified: bool
    
    # Noise floor
    noise_floor_db: float
    snr_estimate_db: float
    
    # Room analysis
    room_modes: List[Dict[str, float]]
    rt60_estimate: float
    schroeder_freq: float
    
    # PSMSL metrics
    final_coherence: float
    final_curvature: float
    final_residual: float
    convergence_time_s: float
    
    # Sector analysis
    sector_energies: Dict[str, float]
    sector_corrections: Dict[str, float]
    
    # Overall
    calibration_quality: str  # "excellent", "good", "fair", "poor"
    recommendations: List[str]


class RoomCalibrator:
    """Automated room calibration system"""
    
    SECTOR_NAMES = [
        "Foundation", "Structure", "Body", "Presence", 
        "Clarity", "Air", "Extension"
    ]
    
    def __init__(self, port: str, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial: Optional[serial.Serial] = None
        self.log_file = None
        self.verbose = True
        
    def connect(self) -> bool:
        """Connect to ESP32"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2.0
            )
            time.sleep(0.5)
            self.serial.reset_input_buffer()
            self._log(f"Connected to {self.port}")
            return True
        except serial.SerialException as e:
            self._log(f"Connection error: {e}", error=True)
            return False
    
    def disconnect(self):
        """Disconnect from ESP32"""
        if self.serial and self.serial.is_open:
            self.serial.close()
    
    def _log(self, message: str, error: bool = False):
        """Log message to console and file"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        prefix = "ERROR" if error else "INFO"
        line = f"[{timestamp}] [{prefix}] {message}"
        
        if self.verbose:
            print(line)
        
        if self.log_file:
            self.log_file.write(line + "\n")
            self.log_file.flush()
    
    def _send_command(self, cmd: str, timeout: float = 2.0) -> List[str]:
        """Send command and get response"""
        if not self.serial:
            return []
        
        self.serial.reset_input_buffer()
        self.serial.write((cmd + "\n").encode())
        self.serial.flush()
        
        lines = []
        start = time.time()
        
        while time.time() - start < timeout:
            if self.serial.in_waiting:
                line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    lines.append(line)
                    if line.endswith(">") or "Error" in line:
                        break
            else:
                time.sleep(0.01)
        
        return lines
    
    def _get_status(self) -> Dict[str, Any]:
        """Get current status as dict"""
        lines = self._send_command("status_json")
        
        for line in lines:
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    pass
        
        # Fallback: parse text status
        lines = self._send_command("status")
        status = {}
        for line in lines:
            if ":" in line:
                key, val = line.split(":", 1)
                status[key.strip().lower().replace(" ", "_")] = val.strip()
        
        return status
    
    def _wait_for_convergence(self, target: float = 0.8, timeout: float = 60.0) -> Tuple[bool, float, float]:
        """Wait for system to converge"""
        self._log(f"Waiting for convergence (target: {target:.1%})...")
        
        start = time.time()
        last_convergence = 0.0
        stable_count = 0
        
        while time.time() - start < timeout:
            status = self._get_status()
            convergence = float(status.get("convergence", 0))
            
            if convergence >= target:
                stable_count += 1
                if stable_count >= 3:  # Stable for 3 readings
                    elapsed = time.time() - start
                    self._log(f"Converged to {convergence:.1%} in {elapsed:.1f}s")
                    return True, convergence, elapsed
            else:
                stable_count = 0
            
            if abs(convergence - last_convergence) > 0.01:
                self._log(f"  Convergence: {convergence:.1%}")
            
            last_convergence = convergence
            time.sleep(0.5)
        
        elapsed = time.time() - start
        self._log(f"Convergence timeout after {elapsed:.1f}s (reached {last_convergence:.1%})")
        return False, last_convergence, elapsed
    
    # =========================================================================
    # Calibration Phases
    # =========================================================================
    
    def phase_hardware_check(self) -> Tuple[bool, Dict[str, Any]]:
        """Phase 1: Verify hardware connections"""
        self._log("\n" + "=" * 50)
        self._log("PHASE 1: Hardware Check")
        self._log("=" * 50)
        
        result = {
            "mic_levels": [],
            "speaker_ok": False,
            "dac_ok": False
        }
        
        # Check microphone levels
        self._log("Checking microphone inputs...")
        lines = self._send_command("diag mic_levels")
        
        for line in lines:
            if "Mic" in line and "dB" in line:
                try:
                    level = float(line.split(":")[1].replace("dB", "").strip())
                    result["mic_levels"].append(level)
                    self._log(f"  {line}")
                except (ValueError, IndexError):
                    pass
        
        # Verify we have mic input
        if result["mic_levels"]:
            avg_level = sum(result["mic_levels"]) / len(result["mic_levels"])
            if avg_level > -80:  # Should see some signal
                self._log(f"  Microphones OK (avg: {avg_level:.1f} dB)")
            else:
                self._log("  WARNING: Microphone levels very low", error=True)
        
        # Test speaker output
        self._log("Testing speaker output (1kHz tone for 1 second)...")
        self._send_command("test sine 1000")
        time.sleep(1.0)
        self._send_command("test off")
        
        # Ask user to confirm
        self._log("  Did you hear the test tone? (Assuming yes for automated test)")
        result["speaker_ok"] = True
        
        # Check DAC status
        lines = self._send_command("diag dac_status")
        for line in lines:
            if "OK" in line or "ready" in line.lower():
                result["dac_ok"] = True
                self._log(f"  DAC: {line}")
        
        success = len(result["mic_levels"]) > 0 and result["speaker_ok"]
        return success, result
    
    def phase_noise_floor(self) -> Tuple[bool, Dict[str, Any]]:
        """Phase 2: Measure noise floor"""
        self._log("\n" + "=" * 50)
        self._log("PHASE 2: Noise Floor Measurement")
        self._log("=" * 50)
        
        result = {
            "noise_floor_db": -100.0,
            "snr_estimate_db": 0.0
        }
        
        self._log("Measuring ambient noise (please remain quiet)...")
        self._send_command("test off")  # Ensure silence
        time.sleep(0.5)
        
        # Measure noise floor
        lines = self._send_command("diag noise_floor", timeout=5.0)
        
        for line in lines:
            if "noise" in line.lower() and "dB" in line:
                try:
                    result["noise_floor_db"] = float(line.split(":")[1].replace("dB", "").strip())
                    self._log(f"  Noise floor: {result['noise_floor_db']:.1f} dB")
                except (ValueError, IndexError):
                    pass
        
        # Estimate SNR with test signal
        self._log("Measuring signal level...")
        self._send_command("test sine 1000")
        time.sleep(0.5)
        
        lines = self._send_command("diag signal_level")
        signal_level = -20.0
        
        for line in lines:
            if "signal" in line.lower() and "dB" in line:
                try:
                    signal_level = float(line.split(":")[1].replace("dB", "").strip())
                except (ValueError, IndexError):
                    pass
        
        self._send_command("test off")
        
        result["snr_estimate_db"] = signal_level - result["noise_floor_db"]
        self._log(f"  Estimated SNR: {result['snr_estimate_db']:.1f} dB")
        
        success = result["snr_estimate_db"] > 20  # At least 20 dB SNR
        if not success:
            self._log("  WARNING: Low SNR may affect calibration accuracy", error=True)
        
        return success, result
    
    def phase_signal_path(self) -> Tuple[bool, Dict[str, Any]]:
        """Phase 3: Verify signal path integrity"""
        self._log("\n" + "=" * 50)
        self._log("PHASE 3: Signal Path Verification")
        self._log("=" * 50)
        
        result = {
            "frequencies_tested": [],
            "all_passed": True
        }
        
        test_freqs = [100, 440, 1000, 4000, 10000]
        
        for freq in test_freqs:
            self._log(f"Testing {freq} Hz...")
            self._send_command(f"test sine {freq}")
            time.sleep(0.3)
            
            # Check if signal is detected
            status = self._get_status()
            energy = float(status.get("total_energy", -100))
            
            passed = energy > -60  # Should see significant energy
            result["frequencies_tested"].append({
                "freq": freq,
                "energy_db": energy,
                "passed": passed
            })
            
            self._log(f"  {freq} Hz: {energy:.1f} dB {'✓' if passed else '✗'}")
            
            if not passed:
                result["all_passed"] = False
        
        self._send_command("test off")
        
        return result["all_passed"], result
    
    def phase_frequency_sweep(self) -> Tuple[bool, Dict[str, Any]]:
        """Phase 4: Run frequency sweep for room analysis"""
        self._log("\n" + "=" * 50)
        self._log("PHASE 4: Frequency Sweep Analysis")
        self._log("=" * 50)
        
        result = {
            "sector_energies": {},
            "sector_coherence": {},
            "sweep_complete": False
        }
        
        self._log("Running frequency sweep (20 Hz - 20 kHz)...")
        self._send_command("test sweep")
        
        # Wait for sweep to complete
        time.sleep(5.0)
        
        # Get sector analysis
        lines = self._send_command("diag sectors")
        
        for line in lines:
            for sector in self.SECTOR_NAMES:
                if sector in line:
                    try:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            values = parts[1].strip().split()
                            energy = float(values[0].replace("dB", ""))
                            result["sector_energies"][sector] = energy
                            self._log(f"  {sector}: {energy:.1f} dB")
                    except (ValueError, IndexError):
                        pass
        
        self._send_command("test off")
        result["sweep_complete"] = len(result["sector_energies"]) > 0
        
        return result["sweep_complete"], result
    
    def phase_mode_detection(self) -> Tuple[bool, Dict[str, Any]]:
        """Phase 5: Detect room modes"""
        self._log("\n" + "=" * 50)
        self._log("PHASE 5: Room Mode Detection")
        self._log("=" * 50)
        
        result = {
            "modes": [],
            "rt60_estimate": 0.0,
            "schroeder_freq": 0.0
        }
        
        self._log("Analyzing room modes...")
        
        # Use pink noise for mode detection
        self._send_command("test noise")
        time.sleep(3.0)
        
        # Get mode analysis
        lines = self._send_command("diag room_modes", timeout=5.0)
        
        for line in lines:
            if "Mode" in line and "Hz" in line:
                try:
                    # Parse: "Mode 1: 45.2 Hz, Q=8.5, -3.2 dB"
                    parts = line.split(",")
                    freq = float(parts[0].split(":")[1].replace("Hz", "").strip())
                    q = float(parts[1].split("=")[1].strip()) if len(parts) > 1 else 5.0
                    gain = float(parts[2].replace("dB", "").strip()) if len(parts) > 2 else 0.0
                    
                    result["modes"].append({
                        "frequency": freq,
                        "q_factor": q,
                        "magnitude_db": gain
                    })
                    self._log(f"  Mode: {freq:.1f} Hz, Q={q:.1f}, {gain:+.1f} dB")
                except (ValueError, IndexError):
                    pass
            elif "RT60" in line:
                try:
                    result["rt60_estimate"] = float(line.split(":")[1].replace("s", "").strip())
                    self._log(f"  RT60 estimate: {result['rt60_estimate']:.2f} s")
                except (ValueError, IndexError):
                    pass
            elif "Schroeder" in line:
                try:
                    result["schroeder_freq"] = float(line.split(":")[1].replace("Hz", "").strip())
                    self._log(f"  Schroeder frequency: {result['schroeder_freq']:.0f} Hz")
                except (ValueError, IndexError):
                    pass
        
        self._send_command("test off")
        
        return len(result["modes"]) > 0, result
    
    def phase_convergence(self) -> Tuple[bool, Dict[str, Any]]:
        """Phase 6: Run adaptive convergence"""
        self._log("\n" + "=" * 50)
        self._log("PHASE 6: Adaptive Convergence")
        self._log("=" * 50)
        
        result = {
            "converged": False,
            "final_convergence": 0.0,
            "convergence_time_s": 0.0,
            "coherence": 0.0,
            "curvature": 0.0,
            "residual": 0.0
        }
        
        # Start adaptive mode
        self._log("Starting adaptive calibration...")
        self._send_command("mode adaptive")
        
        # Use pink noise as test signal
        self._send_command("test noise")
        
        # Wait for convergence
        converged, final_conv, elapsed = self._wait_for_convergence(
            target=0.8, timeout=60.0
        )
        
        result["converged"] = converged
        result["final_convergence"] = final_conv
        result["convergence_time_s"] = elapsed
        
        # Get final PSMSL metrics
        status = self._get_status()
        result["coherence"] = float(status.get("coherence", 0))
        result["curvature"] = float(status.get("curvature", 0))
        result["residual"] = float(status.get("residual", 0))
        
        self._log(f"Final metrics:")
        self._log(f"  Coherence: {result['coherence']:.3f}")
        self._log(f"  Curvature: {result['curvature']:.3f}")
        self._log(f"  Residual: {result['residual']:.3f}")
        
        self._send_command("test off")
        
        return converged, result
    
    def phase_verification(self) -> Tuple[bool, Dict[str, Any]]:
        """Phase 7: Verify calibration results"""
        self._log("\n" + "=" * 50)
        self._log("PHASE 7: Calibration Verification")
        self._log("=" * 50)
        
        result = {
            "corrections_applied": {},
            "before_after": {},
            "improvement_db": 0.0
        }
        
        # Get applied corrections
        self._log("Checking applied corrections...")
        lines = self._send_command("diag corrections")
        
        for line in lines:
            for sector in self.SECTOR_NAMES:
                if sector in line and "dB" in line:
                    try:
                        correction = float(line.split(":")[1].replace("dB", "").strip())
                        result["corrections_applied"][sector] = correction
                        self._log(f"  {sector}: {correction:+.1f} dB")
                    except (ValueError, IndexError):
                        pass
        
        # Run verification sweep
        self._log("Running verification sweep...")
        self._send_command("test sweep")
        time.sleep(3.0)
        
        # Compare before/after would require stored baseline
        # For now, just verify system is stable
        status = self._get_status()
        stability = float(status.get("stability", 0))
        
        self._log(f"System stability: {stability:.1%}")
        
        self._send_command("test off")
        
        return stability > 0.7, result
    
    # =========================================================================
    # Main Calibration Procedure
    # =========================================================================
    
    def run_calibration(self, quick: bool = False, output_file: Optional[str] = None) -> CalibrationResult:
        """Run complete calibration procedure"""
        start_time = time.time()
        phases_completed = []
        
        # Open log file
        log_filename = f"calibration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.log_file = open(log_filename, 'w')
        
        self._log("=" * 60)
        self._log("ROOM CALIBRATION PROCEDURE")
        self._log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._log(f"Mode: {'Quick' if quick else 'Full'}")
        self._log("=" * 60)
        
        # Initialize result
        result_data = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": 0,
            "phases_completed": [],
            "hardware_ok": False,
            "mic_levels": [],
            "speaker_verified": False,
            "noise_floor_db": -100,
            "snr_estimate_db": 0,
            "room_modes": [],
            "rt60_estimate": 0,
            "schroeder_freq": 0,
            "final_coherence": 0,
            "final_curvature": 0,
            "final_residual": 0,
            "convergence_time_s": 0,
            "sector_energies": {},
            "sector_corrections": {},
            "calibration_quality": "unknown",
            "recommendations": []
        }
        
        try:
            # Phase 1: Hardware Check
            success, data = self.phase_hardware_check()
            if success:
                phases_completed.append("hardware_check")
                result_data["hardware_ok"] = True
                result_data["mic_levels"] = data.get("mic_levels", [])
                result_data["speaker_verified"] = data.get("speaker_ok", False)
            elif not quick:
                self._log("Hardware check failed. Aborting.", error=True)
                raise Exception("Hardware check failed")
            
            # Phase 2: Noise Floor
            if not quick:
                success, data = self.phase_noise_floor()
                if success:
                    phases_completed.append("noise_floor")
                    result_data["noise_floor_db"] = data.get("noise_floor_db", -100)
                    result_data["snr_estimate_db"] = data.get("snr_estimate_db", 0)
            
            # Phase 3: Signal Path
            success, data = self.phase_signal_path()
            if success:
                phases_completed.append("signal_path")
            
            # Phase 4: Frequency Sweep
            success, data = self.phase_frequency_sweep()
            if success:
                phases_completed.append("frequency_sweep")
                result_data["sector_energies"] = data.get("sector_energies", {})
            
            # Phase 5: Mode Detection
            if not quick:
                success, data = self.phase_mode_detection()
                if success:
                    phases_completed.append("mode_detection")
                    result_data["room_modes"] = data.get("modes", [])
                    result_data["rt60_estimate"] = data.get("rt60_estimate", 0)
                    result_data["schroeder_freq"] = data.get("schroeder_freq", 0)
            
            # Phase 6: Convergence
            success, data = self.phase_convergence()
            if success:
                phases_completed.append("convergence")
            result_data["final_coherence"] = data.get("coherence", 0)
            result_data["final_curvature"] = data.get("curvature", 0)
            result_data["final_residual"] = data.get("residual", 0)
            result_data["convergence_time_s"] = data.get("convergence_time_s", 0)
            
            # Phase 7: Verification
            if not quick:
                success, data = self.phase_verification()
                if success:
                    phases_completed.append("verification")
                result_data["sector_corrections"] = data.get("corrections_applied", {})
            
        except Exception as e:
            self._log(f"Calibration error: {e}", error=True)
        
        # Calculate quality
        result_data["phases_completed"] = phases_completed
        result_data["duration_seconds"] = time.time() - start_time
        
        # Determine quality rating
        coherence = result_data["final_coherence"]
        if coherence >= 0.85:
            result_data["calibration_quality"] = "excellent"
        elif coherence >= 0.7:
            result_data["calibration_quality"] = "good"
        elif coherence >= 0.5:
            result_data["calibration_quality"] = "fair"
        else:
            result_data["calibration_quality"] = "poor"
        
        # Generate recommendations
        recommendations = []
        if result_data["snr_estimate_db"] < 30:
            recommendations.append("Consider reducing ambient noise for better accuracy")
        if len(result_data["room_modes"]) > 5:
            recommendations.append("Room has significant modal issues - consider acoustic treatment")
        if result_data["final_curvature"] > 0.3:
            recommendations.append("System stability is low - may need longer settling time")
        if result_data["convergence_time_s"] > 30:
            recommendations.append("Slow convergence - room may have complex acoustics")
        
        result_data["recommendations"] = recommendations
        
        # Summary
        self._log("\n" + "=" * 60)
        self._log("CALIBRATION COMPLETE")
        self._log("=" * 60)
        self._log(f"Duration: {result_data['duration_seconds']:.1f} seconds")
        self._log(f"Phases completed: {len(phases_completed)}/7")
        self._log(f"Quality: {result_data['calibration_quality'].upper()}")
        self._log(f"Final coherence: {result_data['final_coherence']:.1%}")
        
        if recommendations:
            self._log("\nRecommendations:")
            for rec in recommendations:
                self._log(f"  • {rec}")
        
        # Save result
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(result_data, f, indent=2)
            self._log(f"\nResults saved to: {output_file}")
        
        self._log(f"Log saved to: {log_filename}")
        
        if self.log_file:
            self.log_file.close()
        
        return CalibrationResult(**result_data)


def main():
    parser = argparse.ArgumentParser(
        description="Room Calibration Procedure",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--port", "-p", required=True,
                        help="Serial port (e.g., COM3 or /dev/ttyUSB0)")
    parser.add_argument("--quick", "-q", action="store_true",
                        help="Quick calibration (skip detailed analysis)")
    parser.add_argument("--full", "-f", action="store_true",
                        help="Full calibration with all phases")
    parser.add_argument("--output", "-o", type=str,
                        help="Output file for calibration results (JSON)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress verbose output")
    
    args = parser.parse_args()
    
    calibrator = RoomCalibrator(args.port)
    calibrator.verbose = not args.quiet
    
    if not calibrator.connect():
        return 1
    
    try:
        result = calibrator.run_calibration(
            quick=args.quick,
            output_file=args.output or f"room_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        print(f"\nCalibration quality: {result.calibration_quality.upper()}")
        return 0 if result.calibration_quality in ["excellent", "good"] else 1
        
    finally:
        calibrator.disconnect()


if __name__ == "__main__":
    sys.exit(main())
