    import time
    import socket
    import pymcprotocol

    # --- PLC connection ---
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

    # --- Handshake helpers ---
    def first_handshake():
        mc.batchwrite_bitunits(headdevice="Y1E", values=[1]); time.sleep(0.5)
        mc.batchwrite_bitunits(headdevice="Y1E", values=[0]); time.sleep(0.5)

    def second_handshake_read(address):
        mc.batchwrite_bitunits(headdevice="Y1E", values=[1]); time.sleep(0.5)
        val = mc.batchread_bitunits(headdevice=address, readsize=1)[0]
        return 1 if int(val) == 1 else 0

    def select_job(y1a, y1c, y18):
        mc.batchwrite_bitunits(headdevice="Y1A", values=[int(y1a)])
        mc.batchwrite_bitunits(headdevice="Y1C", values=[int(y1c)])
        mc.batchwrite_bitunits(headdevice="Y18", values=[int(y18)])

    def run_and_store(label, read_address, memory_coil):
        first_handshake()
        val = second_handshake_read(read_address)
        print(f"{label} read {read_address} value =", val)
        mc.batchwrite_bitunits(headdevice=memory_coil, values=[int(val)])
        print(f"Stored {label} result into {memory_coil}")
        mc.batchwrite_bitunits(headdevice="Y1E", values=[0])

    def drive_lights_by_flags():
        tray_empty = int(mc.batchread_bitunits(headdevice="M200", readsize=1)[0]) == 1
        pass_any = (int(mc.batchread_bitunits(headdevice="M300", readsize=1)[0]) == 1) or \
                (int(mc.batchread_bitunits(headdevice="M301", readsize=1)[0]) == 1)
        fail_any = (int(mc.batchread_bitunits(headdevice="M400", readsize=1)[0]) == 1) or \
                (int(mc.batchread_bitunits(headdevice="M401", readsize=1)[0]) == 1)

        if tray_empty:
            print("Tray Empty → Alarm Y12 ON")
            mc.batchwrite_bitunits(headdevice="Y12", values=[1]); time.sleep(1)
            mc.batchwrite_bitunits(headdevice="Y12", values=[0])
        if pass_any:
            print("PASS → Green Light Y11 ON")
            mc.batchwrite_bitunits(headdevice="Y11", values=[1]); time.sleep(1)
            mc.batchwrite_bitunits(headdevice="Y11", values=[0])
        if fail_any:
            print("FAIL → Red Light Y10 ON")
            mc.batchwrite_bitunits(headdevice="Y10", values=[1]); time.sleep(1)
            mc.batchwrite_bitunits(headdevice="Y10", values=[0])

    def reset_for_next_cycle():
        mc.batchwrite_bitunits(headdevice="Y1E", values=[0])
        mc.batchwrite_bitunits(headdevice="M200", values=[0])
        mc.batchwrite_bitunits(headdevice="M300", values=[0])
        mc.batchwrite_bitunits(headdevice="M301", values=[0])
        mc.batchwrite_bitunits(headdevice="M400", values=[0])
        mc.batchwrite_bitunits(headdevice="M401", values=[0])
        mc.batchwrite_bitunits(headdevice="M210", values=[0])
        mc.batchwrite_bitunits(headdevice="M211", values=[0])
        mc.batchwrite_bitunits(headdevice="M212", values=[0])
        mc.batchwrite_bitunits(headdevice="M213", values=[0])

    def main():
        connect_plc()
        print("Connected to PLC, waiting for M100 to start cycle...")

        while True:
            try:
                if int(mc.batchread_bitunits(headdevice="M100", readsize=1)[0]) == 1:
                    print("Start detected → Begin sequence")

                    # --- Job1: Tray check ---
                    select_job(1,0,0)
                    run_and_store("Job1 Tray","X0E","M210")

                    if int(mc.batchread_bitunits(headdevice="M210", readsize=1)[0]) == 1:
                        print("Job1 PASS → Tray Empty → M200 ON")
                        mc.batchwrite_bitunits(headdevice="M200", values=[1])
                    else:
                        print("Tray NOT empty → Proceed to Job2")

                        # --- Job2: Color check ---
                        select_job(0,1,0)
                        run_and_store("Job2 Color","X06","M211")

                        if int(mc.batchread_bitunits(headdevice="M211", readsize=1)[0]) == 1:
                            print("Job2 → Orange detected → Proceed to Job3")

                            # --- Job3: Orange pass/fail ---
                            select_job(0,1,1)
                            run_and_store("Job3 Orange","X0E","M212")

                            if int(mc.batchread_bitunits(headdevice="M212", readsize=1)[0]) == 1:
                                print("Job3 PASS → Orange Pass → M300 ON")
                                mc.batchwrite_bitunits(headdevice="M300", values=[1])
                            else:
                                print("Job3 FAIL → Orange Fail → M400 ON")
                                mc.batchwrite_bitunits(headdevice="M400", values=[1])

                        else:
                            print("Job2 → Brown detected → Proceed to Job4")

                            # --- Job4: Brown pass/fail ---
                            select_job(1,0,0)
                            run_and_store("Job4 Brown","X06","M213")

                            if int(mc.batchread_bitunits(headdevice="M213", readsize=1)[0]) == 1:
                                print("Job4 PASS → Brown Pass → M301 ON")
                                mc.batchwrite_bitunits(headdevice="M301", values=[1])
                            else:
                                print("Job4 FAIL → Brown Fail → M401 ON")
                                mc.batchwrite_bitunits(headdevice="M401", values=[1])

                    drive_lights_by_flags()

                    mc.batchwrite_bitunits(headdevice="M100", values=[0])
                    mc.batchwrite_bitunits(headdevice="M101", values=[1])

                    reset_for_next_cycle()

                    time.sleep(0.5)
                    print("Cycle complete → M101 ON, all flags and M210–M213 cleared, waiting for next M100")

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
