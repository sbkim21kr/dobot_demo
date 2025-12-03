import time
import socket
import threading
import pymcprotocol
import DobotDllType as dType

# =========================================================
# CONFIGURATION
# =========================================================

# PLC Config - Using confirmed working IP/Port
PLC_IP = "192.168.3.39"
PLC_PORT = 5051
PLC_TIMEOUT = 5.0  # Timeout in seconds for connection and data transfer

# Dobot Config
DOBOT_PORT = "COM4"
BAUDRATE = 115200

# SETTING CONSERVATIVE GLOBAL VELOCITY AND ACCELERATION
# These are applied to both joint space (Common) and Cartesian space (Coordinate)
DOBOT_VELOCITY = 50.0 
DOBOT_ACCELERATION = 50.0
# For reference: Maximum values are typically around 200/200

# =========================================================
# DATA FROM CSV
# =========================================================
# Format: (X, Y, Z, R, Velocity, Acceleration, Suction, Dwell)

WAYPOINTS = [
    (101.311,-114.5566,12.1601,-48.5113,0.0,0.0,0,0.0),
    (125.7218,-142.159,47.3133,-48.5113,0.0,0.0,0,0.0),
    (101.311,-114.5566,12.1601,-48.5113,0.0,0.0,0,0.0)
]

# =========================================================
# PLC FUNCTIONS
# =========================================================

def connect_plc():
    # Uses the simple constructor for robustness across pymcprotocol versions.
    mc = pymcprotocol.Type3E()
    while True:
        try:
            print(f"[PLC] Attempting connection to {PLC_IP}:{PLC_PORT}...")
            mc.connect(PLC_IP, PLC_PORT)
            print(f"[PLC] Connected successfully to {PLC_IP}:{PLC_PORT}")
            return mc
        except Exception as e:
            print(f"[PLC] Connection Error: {e}")
            print("[PLC] Retrying in 2 seconds...")
            time.sleep(2)

def set_plc_bit(mc, address, value):
    """Sets a PLC bit address to a specific value (1 for ON, 0 for OFF)."""
    try:
        mc.batchwrite_bitunits(headdevice=address, values=[value])
        print(f"[PLC] Set {address} to {'ON' if value else 'OFF'}")
    except Exception as e:
        print(f"[PLC] Error setting {address} to {value}: {e}")

def pulse_bit_plc(mc, address, on_time=0.2, off_time=0.2):
    """Turns a PLC bit ON, waits, then turns it OFF."""
    try:
        mc.batchwrite_bitunits(headdevice=address, values=[1])
        print(f"[PLC] Pulse {address} → ON {on_time}s")
        time.sleep(on_time)
        mc.batchwrite_bitunits(headdevice=address, values=[0])
        print(f"[PLC] Pulse {address} → OFF {off_time}s")
        # Wait the off time to allow PLC to process the pulse cycle
        time.sleep(off_time) 
    except Exception as e:
        print(f"[PLC] Error pulsing {address}: {e}")

def read_plc_bit(mc, address):
    """Reads the state of a single PLC bit address."""
    try:
        val = mc.batchread_bitunits(headdevice=address, readsize=1)[0]
        return int(val)
    except Exception as e:
        print(f"[PLC] Error reading {address}: {e}")
        return 0

# =========================================================
# DOBOT FUNCTIONS
# =========================================================

def run_dobot_sequence(api):
    print("[DOBOT] Starting sequence based on CSV data...")
    
    # Clean queue before starting
    dType.SetQueuedCmdClear(api)
    
    lastIndex = 0
    
    # Iterate through the CSV points
    for i, (x, y, z, r, vel, accel, suction, dwell) in enumerate(WAYPOINTS):
        
        # 1. Handle Velocity/Acceleration (Optional) - using global V/A
        
        # 2. Queue the Movement
        # Reverted to the correct enum structure and keyword argument syntax
        # confirmed by the user's working script. Using PTPMOVLXYZMode.
        
        lastIndex = dType.SetPTPCmd(api, 
                                    dType.PTPMode.PTPMOVLXYZMode, # Mode 3: Linear move in Cartesian space
                                    x, y, z, r, 
                                    isQueued=1)[0]
        
        # 3. Handle Suction
        # EnableCtrl=1, Suction=suction_val, isQueued=1
        dType.SetEndEffectorSuctionCup(api, 1, int(suction), 1)

        # 4. Handle Dwell Time (Delay)
        # Note: This executes the sleep on the host PC, not inside the Dobot queue.
        if dwell > 0.0:
            print(f"[DOBOT] Dwell time: {dwell}s")
            time.sleep(dwell)

        print(f"[DOBOT] Queued Point {i+1}: X={x}, Y={y}, Z={z}, R={r}, Suc={suction}, Dwell={dwell}")

    # Execute the queue
    dType.SetQueuedCmdStartExec(api)

    # Wait for completion of the last queued command
    while lastIndex > dType.GetQueuedCmdCurrentIndex(api)[0]:
        dType.dSleep(100)

    # Stop execution loop
    dType.SetQueuedCmdStopExec(api)
    print("[DOBOT] Sequence Finished.")

# =========================================================
# MAIN LOOP
# =========================================================

def main():
    # 1. Connect to Dobot
    api = dType.load()
    state = dType.ConnectDobot(api, DOBOT_PORT, BAUDRATE)[0]
    
    if state != dType.DobotConnect.DobotConnect_NoError:
        print(f"[ERROR] Could not connect to Dobot on {DOBOT_PORT}")
        return

    print("[DOBOT] Robot Connected.")
    dType.SetQueuedCmdClear(api)
    
    # 2. Set conservative global PTP Common Parameters (Joint Velocity/Acceleration)
    dType.SetPTPCommonParams(api, DOBOT_VELOCITY, DOBOT_ACCELERATION, isQueued=0)
    
    # Set conservative global PTP Coordinate Parameters (Cartesian Velocity/Acceleration)
    # The function requires four speed/acceleration values (XYZ V/A and R V/A).
    dType.SetPTPCoordinateParams(api, DOBOT_VELOCITY, DOBOT_ACCELERATION, DOBOT_VELOCITY, DOBOT_ACCELERATION, isQueued=0)
    print(f"[DOBOT] Set global V/A (Joint & Cartesian) to: {DOBOT_VELOCITY} / {DOBOT_ACCELERATION}")
    
    # Optional: Home the robot if needed
    # dType.SetHOMECmd(api, temp=0, isQueued=1)

    # 3. Connect to PLC
    mc = connect_plc()

    print("System Ready. Waiting for M100 pulse to start the job...")

    try:
        while True:
            # Check M100 (Start Signal) to start the cycle
            m100_val = read_plc_bit(mc, "M100")

            if m100_val == 1:
                print("\n[EVENT] M100 Detected ON! Starting Dobot sequence.")
                
                # NEW Step 1: Set M101 ON (Dobot Busy)
                set_plc_bit(mc, "M101", 1)
                
                # Step 2: Run Dobot Sequence (synchronous)
                run_dobot_sequence(api)

                # NEW Step 3: Set M101 OFF (Dobot Ready)
                set_plc_bit(mc, "M101", 0)

                # NEW Step 4: Pulse M102 ON (Job Complete Signal)
                print("[SYSTEM] Dobot work complete. Pulsing M102 ON.")
                pulse_bit_plc(mc, "M102") 

                print("[SYSTEM] Waiting for M100 to reset...")
                
                # Debounce: Wait until PLC turns M100 OFF before allowing the next trigger
                while read_plc_bit(mc, "M100") == 1:
                    time.sleep(0.5)
                
                print("[SYSTEM] Ready for next cycle.")

            time.sleep(0.2) # Polling interval

    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Runtime error: {e}")
    finally:
        # Cleanup
        dType.DisconnectDobot(api)
        # Attempt to close the PLC connection if it was successfully opened
        if 'mc' in locals():
            try:
                mc.close()
            except:
                pass 
        print("Connections closed.")

if __name__ == "__main__":
    main()