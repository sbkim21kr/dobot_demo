import DobotDllType as dType

api = dType.load()
state = dType.ConnectDobot(api, "", 115200)[0]
print("Connection state:", state)

if state == dType.DobotConnect.DobotConnect_NoError:
    dType.SetQueuedCmdClear(api)

    # Move directly to your home coordinates (X, Y, Z, R)
    lastIndex = dType.SetPTPCmd(api,
                                dType.PTPMode.PTPMOVLXYZMode,
                                60.3, -204.1, 30.9, -34.9,
                                isQueued=1)[0]

    dType.SetQueuedCmdStartExec(api)

    # Wait until the move is done
    while lastIndex > dType.GetQueuedCmdCurrentIndex(api)[0]:
        dType.dSleep(100)

    dType.SetQueuedCmdStopExec(api)

dType.DisconnectDobot(api)
print("Returned to home and disconnected.")
