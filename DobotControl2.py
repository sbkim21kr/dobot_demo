import DobotDllType as dType

api = dType.load()
state = dType.ConnectDobot(api, "", 115200)[0]
print("Connection state:", state)

if state == dType.DobotConnect.DobotConnect_NoError:
    dType.SetQueuedCmdClear(api)

    # Define your waypoints (X, Y, Z, R)
    waypoints = [
        (60.3, -204.1, 30.9, -34.9),
        (68.3, -194, -48.9, -32),
        (79.3, -225.9, 85.1, -32.1),
        (220.9, -93.6, 86.2, 15.6),
        (228.7, -73.8, -30.5, 20.7),
        (65.5, -244.1, 66.2, -36.4),
        (-123.4, -211.8, 77.7, -81.6),
        (-100.1, -227.7, -46.6, -75.1),
        (-82, -241.9, 65.9, -70.1),
        (60.3, -204.1, 30.9, -34.9)  # back to start
    ]

    # Queue moves through all waypoints
    for (x, y, z, r) in waypoints:
        lastIndex = dType.SetPTPCmd(api,
                                    dType.PTPMode.PTPMOVLXYZMode,
                                    x, y, z, r,
                                    isQueued=1)[0]

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
