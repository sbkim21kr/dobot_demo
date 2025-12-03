import DobotDllType as dType
import sys

COM_PORT = "COM4"
BAUD_RATE = 115200

# Waypoints to follow (X, Y, Z, R, Suction/Gripper status)
WAYPOINTS = [
    (129.0618, 0.0, 5.4539, 0.0001, 0),
    (193.4919, 0.0001, -10.8515, 0.0001, 0),
    (146.6434, 0.0, -26.5536, 0.0001, 0)
]

if __name__ == "__main__":
    api = dType.load()
    print(f"Connecting to Dobot on {COM_PORT}...")
    state = dType.ConnectDobot(api, COM_PORT, BAUD_RATE)[0]

    if state == dType.DobotConnect.DobotConnect_NoError:
        dType.SetQueuedCmdClear(api)
        dType.SetQueuedCmdStartExec(api)

        # --- Factory Homing ---
        print("Sending Factory Homing Command...")
        lastIndex = dType.SetHOMECmd(api, temp=0, isQueued=1)[0]

        # Wait until homing completes
        while lastIndex > dType.GetQueuedCmdCurrentIndex(api)[0]:
            dType.dSleep(200)

        print("✅ Factory Homing finished. Executing waypoints...")

        # --- Waypoints Execution ---
        SAFE_VEL = 20.0   # slow velocity
        SAFE_ACC = 20.0   # slow acceleration

        for i, (x, y, z, r, suction) in enumerate(WAYPOINTS):
            print(f"[{i+1}/{len(WAYPOINTS)}] Moving to X:{x:.2f} Y:{y:.2f} Z:{z:.2f} R:{r:.2f}")

            # Set safe velocity/acceleration
            lastIndex = dType.SetPTPCommonParams(api, SAFE_VEL, SAFE_ACC, isQueued=1)[0]

            # End effector control
            suction_on = 1 if suction == 1 else 0
            lastIndex = dType.SetEndEffectorSuctionCup(api, 1, suction_on, isQueued=1)[0]

            # PTP movement (joint mode for safer motion)
            lastIndex = dType.SetPTPCmd(api,
                                        dType.PTPMode.PTPMOVJXYZMode,
                                        x, y, z, r,
                                        isQueued=1)[0]

        # Wait until last waypoint completes
        while lastIndex > dType.GetQueuedCmdCurrentIndex(api)[0]:
            dType.dSleep(100)

        dType.SetQueuedCmdStopExec(api)

        pose = dType.GetPose(api)
        print("✅ Sequence Finished.")
        print(f"Final Pose: X={pose[0]:.2f}, Y={pose[1]:.2f}, Z={pose[2]:.2f}, R={pose[3]:.2f}")

    else:
        print("❌ Could not connect to Dobot. Check COM port and power.")
        sys.exit(1)

    dType.DisconnectDobot(api)
    print("Connection closed.")
