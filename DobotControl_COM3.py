# DobotControl_COM3.py
import DobotDllType as dType

def run_dobot_com3():
    com_port = "COM3"
    api = dType.load()
    state = dType.ConnectDobot(api, com_port, 115200)[0]
    print(f"[{com_port}] Connect state: {state}")

    try:
        if state == dType.DobotConnect.DobotConnect_NoError:
            dType.SetQueuedCmdClear(api)

            # Waypoints for COM3
            waypoints = [
                (5.2, -212.1, -52.8, -49.96),
                (5.2, -212.1, -63.76, -49.96),
                (5.2, -212.1, 58, -49.96),
                (-87, -193, 58, -75),
                (-87, -193, -63, -75),
                (-87, -193, 63, -75),
                (25, -176, -20, -43.4)
            ]

            for i, (x, y, z, r) in enumerate(waypoints):
                lastIndex = dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, x, y, z, r, isQueued=1)[0]
                if i == 1:
                    dType.SetEndEffectorSuctionCup(api, 1, 1, 1)
                if i == 4:
                    dType.SetEndEffectorSuctionCup(api, 1, 0, 1)

            dType.SetQueuedCmdStartExec(api)
            while lastIndex > dType.GetQueuedCmdCurrentIndex(api)[0]:
                dType.dSleep(100)
            dType.SetQueuedCmdStopExec(api)
        else:
            print(f"[{com_port}] Failed to connect.")
    finally:
        dType.DisconnectDobot(api)
        print(f"[{com_port}] Disconnected.")
