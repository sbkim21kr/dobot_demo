import DobotDllType as dType
import csv
import os
import sys
import time # dSleep is used inside the Dobot module, but time is still useful for general timing

# --- CSV FILE HANDLING FUNCTION ---

def load_waypoints_from_csv(filename):
    """
    Reads waypoints from a CSV file.
    
    The CSV is expected to have the header:
    X,Y,Z,R,Velocity,Acceleration,Suction/Gripper
    
    Returns a list of tuples: [(x, y, z, r, vel, accel, suction_gripper), ...]
    """
    waypoints = []
    
    if not os.path.exists(filename):
        print(f"Error: CSV file not found at '{filename}'")
        return None

    try:
        with open(filename, mode='r', newline='') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            
            for row_index, row in enumerate(reader, start=1):
                try:
                    # Parse the 7 expected columns as float/int
                    x = float(row[0])
                    y = float(row[1])
                    z = float(row[2])
                    r = float(row[3])
                    vel = float(row[4])
                    accel = float(row[5])
                    suction_gripper = int(row[6])
                    
                    # Append the complete waypoint tuple
                    waypoints.append((x, y, z, r, vel, accel, suction_gripper))
                    
                except (ValueError, IndexError) as e:
                    print(f"Skipping row {row_index} due to data format error: {e}. Row data: {row}")
                    continue
        
        return waypoints

    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return None

# --- DOBOT EXECUTION ---

if __name__ == "__main__":
    
    # 1. Configuration
    COM_PORT = "COM4"
    BAUD_RATE = 115200
    CSV_FILENAME = "PreferredOriginAfterHomingForLifting.csv" # Ensure this file is in the same directory

    # 2. Load Waypoints
    print(f"Attempting to load waypoints from '{CSV_FILENAME}'...")
    waypoints_data = load_waypoints_from_csv(CSV_FILENAME)
    
    if not waypoints_data:
        print("🛑 Failed to load waypoints. Terminating script.")
        sys.exit(1)
        
    print(f"✅ Loaded {len(waypoints_data)} waypoints successfully.")

    # 3. Dobot Connection
    api = dType.load()
    state = dType.ConnectDobot(api, COM_PORT, BAUD_RATE)[0]
    print(f"Connection state on {COM_PORT}: {state}")

    if state == dType.DobotConnect.DobotConnect_NoError:
        
        # Clear previous commands and start command queuing mode
        dType.SetQueuedCmdClear(api)
        dType.SetQueuedCmdStartExec(api)

        total_points = len(waypoints_data)
        lastIndex = 0

        # Set default/initial joint and coordinate velocity/acceleration
        # The common parameters will be set inside the loop for dynamic changes.
        dType.SetJOGJointParams(api, 100, 100, 100, 100, isQueued=1)
        dType.SetPTPJointParams(api, 100, 100, 100, 100, isQueued=1)
        
        print("\n--- Sending PTP Sequence Commands to Dobot ---")

        # 4. Queue moves through all waypoints
        for i, wp in enumerate(waypoints_data):
            (x, y, z, r, vel, accel, suction_gripper) = wp
            
            print(f"[{i + 1}/{total_points}] X:{x:.2f} Y:{y:.2f} Z:{z:.2f} R:{r:.2f} | Vel:{vel:.1f} Gripper:{suction_gripper}")

            # A. Set Velocity and Acceleration for THIS specific move
            # Note: This command is queued before the PTP move.
            lastIndex = dType.SetPTPCommonParams(api, vel, accel, isQueued=1)[0]
            
            # B. Control End Effector (Suction)
            # Suction/Gripper status is 1 for ON, 0 for OFF
            suction_on = 1 if suction_gripper == 1 else 0
            lastIndex = dType.SetEndEffectorSuctionCup(api, 1, suction_on, isQueued=1)[0]
            
            # C. Set PTP Movement Command (Linear move in coordinate space)
            lastIndex = dType.SetPTPCmd(api,
                                        dType.PTPMode.PTPMOVLXYZMode,
                                        x, y, z, r,
                                        isQueued=1)[0]
            
        print("--- All commands queued. Waiting for execution... ---")

        # 5. Wait until the last move is done
        while lastIndex > dType.GetQueuedCmdCurrentIndex(api)[0]:
            dType.dSleep(100)
            
        dType.SetQueuedCmdStopExec(api)

        # 6. Print final pose
        pose = dType.GetPose(api)
        print("\n✅ Sequence Finished.")
        print(f"Final coordinates (X, Y, Z, R): {pose[0]:.2f}, {pose[1]:.2f}, {pose[2]:.2f}, {pose[3]:.2f}")

    else:
        print("❌ Could not connect to Dobot. Please check COM port and power.")

    dType.DisconnectDobot(api)
    print("Connection closed.")