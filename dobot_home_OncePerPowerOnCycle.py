import DobotDllType as dType

api = dType.load()
state = dType.ConnectDobot(api, "COM4", 115200)[0]
print("Connection state:", state)

if state == dType.DobotConnect.DobotConnect_NoError:
    dType.SetQueuedCmdClear(api)

    # # Define your preferred home coordinates (X, Y, Z, R)
    # dType.SetHOMEParams(api, 60.3, -204.1, 30.9, -34.9, isQueued=1)

    # Queue the homing command
    lastIndex = dType.SetHOMECmd(api, temp=0, isQueued=1)[0]

    # Start execution
    dType.SetQueuedCmdStartExec(api)

    # Wait until homing is done
    while lastIndex > dType.GetQueuedCmdCurrentIndex(api)[0]:
        dType.dSleep(100)

    dType.SetQueuedCmdStopExec(api)

dType.DisconnectDobot(api)
print("Homing complete and disconnected.")
