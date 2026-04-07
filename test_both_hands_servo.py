#!/usr/bin/env python3
"""
Test script to verify "both hands" servo animation timing and completion.
This script sends the CLOSE_SEQ_ARMS command and measures how long it takes
to complete, watching for the ANIMATION:COMPLETE message from Arduino.
"""

import serial
import time
import sys

def test_both_hands_animation():
    """Test the both hands servo animation with timing measurement."""
    
    # Connect to Arduino serial port
    try:
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
        time.sleep(2)  # Wait for Arduino to initialize
        print(f"✓ Connected to Arduino at /dev/ttyACM0")
    except Exception as e:
        print(f"✗ Failed to connect to Arduino: {e}")
        return False
    
    try:
        # Clear serial buffer
        ser.flushInput()
        print("\nSending CLOSE_SEQ_ARMS command...")
        
        # Send the command that triggers "both hands" animation
        ser.write(b"FINGER:CLOSE_SEQ_ARMS:BOTH\n")
        print(f"[{time.time():.2f}] Command sent at system time")
        
        # Measure how long until ANIMATION:COMPLETE
        start_time = time.time()
        animation_duration = None
        arduino_logs = []
        
        print("\n--- Arduino Serial Output (next 6 seconds) ---")
        while time.time() - start_time < 6.0:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    elapsed = time.time() - start_time
                    print(f"[{elapsed:6.2f}s] {line}")
                    arduino_logs.append((elapsed, line))
                    
                    # Check for completion marker
                    if "ANIMATION:COMPLETE" in line:
                        animation_duration = elapsed
                        print(f"\n✓ ANIMATION:COMPLETE received after {animation_duration:.2f} seconds")
                        break
                    elif "[SERVO]" in line:
                        # Parse timing from servo logs if available
                        if "Phase 3 COMPLETE" in line or "elapsed=" in line:
                            print(f"  >> Key servo phase logged")
        
        if animation_duration is None:
            print("\n⚠ ANIMATION:COMPLETE not received within 6 seconds")
            print("✗ Animation did not complete properly")
            return False
        else:
            print(f"\n✓ Animation completed in {animation_duration:.2f} seconds")
            
            # Expected duration is ~4.08 seconds (2000ms up + 180ms pause + 1900ms down)
            expected_duration = 4.08
            delta = abs(animation_duration - expected_duration)
            
            if delta < 0.3:  # Allow 300ms variance
                print(f"✓ Duration within expected range (expected ~{expected_duration}s, got {animation_duration:.2f}s)")
            else:
                print(f"⚠ Duration differs from expected (expected ~{expected_duration}s, got {animation_duration:.2f}s, delta={delta:.2f}s)")
            
            # Print summary of logs received
            print(f"\nReceived {len(arduino_logs)} log messages from Arduino:")
            for elapsed, msg in arduino_logs:
                if "[SERVO]" in msg or "[CMD]" in msg:
                    print(f"  {elapsed:6.2f}s: {msg[:80]}")
            
            return True
    
    finally:
        ser.close()
        print("\n✓ Serial connection closed")

if __name__ == "__main__":
    print("=" * 60)
    print("  Both Hands Servo Animation Test")
    print("=" * 60)
    success = test_both_hands_animation()
    sys.exit(0 if success else 1)
