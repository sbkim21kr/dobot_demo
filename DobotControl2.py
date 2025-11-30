import DobotDllType as dType

api = dType.load()
state = dType.ConnectDobot(api, "COM4", 115200)[0]
print("Connection state:", state)

if state == dType.DobotConnect.DobotConnect_NoError:
    dType.SetQueuedCmdClear(api)

    # Define your waypoints (X, Y, Z, R)
    waypoints = [
        (5.2, -212.1, -52.8, -49.96),  # Approach wafer
        (5.2, -212.1, -63.76, -49.96),     # Lower to pick
        (5.2, -212.1, 58, -49.96),  # Lift after pick
        (-87, -193, 58, -75),   # Move to place
        (-87, -193, -63, -75),  # Lower to place
        (-87, -193, 63, -75),  # Lift after place
        (25, -176, -20, -43.4)   # back to start
    ]

    # Queue moves through all waypoints
    for i, (x, y, z, r) in enumerate(waypoints):
        lastIndex = dType.SetPTPCmd(api,
                                    dType.PTPMode.PTPMOVLXYZMode,
                                    x, y, z, r,
                                    isQueued=1)[0]

        # Activate suction after reaching pick position
        if i == 1:
            dType.SetEndEffectorSuctionCup(api, 1, 1, 1)

        # Deactivate suction after reaching place position
        if i == 4:
            dType.SetEndEffectorSuctionCup(api, 1, 0, 1)

    # Start execution
    dType.SetQueuedCmdStartExec(api)

    # Wait until the last move is done
    while lastIndex > dType.GetQueuedCmdCurrentIndex(api)[0]:
        dType.dSleep(100)

    dType.SetQueuedCmdStopExec(api)

    # Print final pose
    pose = dType.GetPose(api)
    print("Final coordinates (X, Y, Z, R):", pose[0], pose[1], pose[2], pose[3])

dType.DisconnectDobot(api)
print("Finished path traversal.")
