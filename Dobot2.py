import DobotDllType as dType

# Load Dobot API
api = dType.load()
# Explicitly connect to COM4 at 115200 baud
print("Attempting to connect to Dobot on COM4...")
state = dType.ConnectDobot(api, "COM4", 115200)[0]
print("Connection state:", state)

if state == dType.DobotConnect.DobotConnect_NoError:
    dType.SetQueuedCmdClear(api)

    # Define waypoints: (X, Y, Z, R, vel, accel, gripper, dwell)
    waypoints = [
        (166.5096, -8.6768, -50.3821, 37.917, 15, 15, 0, 300),   # Point1 - start
        (166.5088, -8.6768, 45.8103, 37.917, 35, 35, 0, 200),    # Point2 - transfer
        (136.5861, 95.6279, 45.8103, 75.897, 35, 35, 0, 200),    # Point3 - transfer
        (140.8202, 99.1645, 11.3106, 76.0529, 12, 12, 0, 300),   # Point4 - APPROACH
        (140.8202, 99.1645, 11.3106, 76.0529, 9, 9, 1, 500),     # Point5 - ACTION (gripper close)
        (140.8202, 99.1645, 11.3106, 76.0529, 22, 22, 2, 300),   # Point6 - RETREAT start
        (140.8202, 99.1644, 35.4546, 76.0529, 22, 22, 2, 300),   # Point7 - RETREAT move
        (172.1055, -6.6028, 35.4546, 38.7029, 40, 40, 2, 200),   # Point8 - transfer
        (172.1055, -6.6028, 35.4546, -146.4771, 40, 40, 2, 200), # Point9 - transfer
        (158.0942, -68.3383, 35.4546, -167.6571, 40, 40, 2, 200),# Point10 - transfer
        (179.6473, -77.6549, 32.6332, -167.6571, 40, 40, 2, 200),# Point11 - transfer
        (181.9947, -81.3655, 7.1658, -168.3683, 12, 12, 2, 300), # Point12 - APPROACH
        (181.9947, -81.3655, 7.1658, -168.3683, 9, 9, 1, 500),   # Point13 - ACTION (gripper open/close)
        (167.7602, -75.0016, 12.511, -168.3683, 22, 22, 1, 300), # Point14 - RETREAT move 1
        (167.7605, -75.0017, 35.359, -168.3683, 22, 22, 1, 300), # Point15 - RETREAT move 2
        (183.3615, -12.1413, 35.359, -148.0683, 35, 35, 1, 200), # Point16 - transfer
        (166.5096, -8.6768, -50.3821, 37.917, 15, 15, 0, 300)    # Point17 - return to start
    ]

    # Queue moves through all waypoints
    for i, (x, y, z, r, vel, accel, gripper, dwell) in enumerate(waypoints):
        lastIndex = dType.SetPTPCmd(api,
                                    dType.PTPMode.PTPMOVLXYZMode,
                                    x, y, z, r,
                                    isQueued=1)[0]

        # Gripper control
        if gripper == 1:  # close
            dType.SetEndEffectorGripper(api, 1, 1, isQueued=1)
        elif gripper == 0:  # open
            dType.SetEndEffectorGripper(api, 1, 0, isQueued=1)
        # gripper == 2 means hold, no change

        # Dwell (pause) after each point
        dType.dSleep(dwell)

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
print("Finished path traversal on COM4.")
