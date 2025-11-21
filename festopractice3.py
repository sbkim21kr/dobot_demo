import time
import socket
import pymcprotocol

mc = pymcprotocol.Type3E()
PLC_IP = "192.168.10.100"
PLC_PORT = 5052

def connect_plc():
    while True:
        try:
            mc.connect(PLC_IP, PLC_PORT)
            print(f"Connected to PLC at {PLC_IP}:{PLC_PORT}")
            return
        except Exception as e:
            print("PLC connect error:", e)
            time.sleep(2)

def monitor_y1e():
    status = mc.batchread_bitunits(headdevice="Y1E", readsize=1)[0]
    print(f"[DEBUG] Y1E status = {status}")
    return int(status)

def first_handshake():
    mc.batchwrite_bitunits(headdevice="Y1E", values=[1]); time.sleep(0.2)
    monitor_y1e()
    mc.batchwrite_bitunits(headdevice="Y1E", values=[0]); time.sleep(0.2)
    monitor_y1e()

def second_handshake_read(address):
    mc.batchwrite_bitunits(headdevice="Y1E", values=[1]); time.sleep(0.2)
    monitor_y1e()
    val = mc.batchread_bitunits(headdevice=address, readsize=1)[0]
    mc.batchwrite_bitunits(headdevice="Y1E", values=[0])
    monitor_y1e()
    return int(val)

def select_job(y1a, y1c, y18):
    mc.batchwrite_bitunits(headdevice="Y1A", values=[int(y1a)])
    mc.batchwrite_bitunits(headdevice="Y1C", values=[int(y1c)])
    mc.batchwrite_bitunits(headdevice="Y18", values=[int(y18)])
    print(f"[DEBUG] Job select → Y1A={y1a}, Y1C={y1c}, Y18={y18}")

def main():
    connect_plc()
    print("Connected to PLC, waiting for M100 to start cycle...")

    while True:
        try:
            if int(mc.batchread_bitunits(headdevice="M100", readsize=1)[0]) == 1:
                print("Start detected → Begin sequence")

                # --- Job1: Tray check ---
                select_job(1,0,0)
                first_handshake()
                tray_val = second_handshake_read("X0E")
                print(f"Job1 Tray sensor X0E={tray_val}")

                if tray_val == 1:
                    print("Tray Empty → Alarm Y12 ON")
                    mc.batchwrite_bitunits(headdevice="Y12", values=[1]); time.sleep(1)
                    mc.batchwrite_bitunits(headdevice="Y12", values=[0])
                else:
                    print("Tray NOT empty → Proceed to Job2")

                    # --- Job2: Color check ---
                    select_job(0,1,0)
                    first_handshake()
                    color_val = second_handshake_read("X06")
                    print(f"Job2 Color sensor X06={color_val}")

                    if color_val == 1:
                        print("Orange detected → Y11 ON")
                        mc.batchwrite_bitunits(headdevice="Y11", values=[1]); time.sleep(1)
                        mc.batchwrite_bitunits(headdevice="Y11", values=[0])
                    else:
                        print("Brown detected → Y10 ON")
                        mc.batchwrite_bitunits(headdevice="Y10", values=[1]); time.sleep(1)
                        mc.batchwrite_bitunits(headdevice="Y10", values=[0])

                # Reset cycle flags
                mc.batchwrite_bitunits(headdevice="M100", values=[0])
                mc.batchwrite_bitunits(headdevice="M101", values=[1])
                print("Cycle complete → M101 ON, waiting for next M100")

            time.sleep(0.2)

        except (ConnectionResetError, socket.error) as e:
            print("PLC communication error (socket):", e)
            try: mc.close()
            except: pass
            time.sleep(1)
            connect_plc()
        except Exception as e:
            print("PLC communication error:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
