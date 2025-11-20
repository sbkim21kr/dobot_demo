import time
import pymcprotocol

# --- PLC connection ---
mc = pymcprotocol.Type3E()
mc.connect("192.168.10.100", 5051)  # adjust to your PLC IP/port

# configure the parameters of Melsec PLC including the IP address
# run the script and turn on M100 by setting m100 to 1 in GX works2

# --- Handshake helpers ---
def first_handshake():
    mc.batchwrite_bitunits(["Y1E"], [1]); time.sleep(0.5)
    mc.batchwrite_bitunits(["Y1E"], [0]); time.sleep(0.5)

def second_handshake_read(address):
    mc.batchwrite_bitunits(["Y1E"], [1]); time.sleep(0.5)
    val = mc.batchread_bitunits(address, 1)[0]
    return 1 if val == 1 else 0

def select_job(y1a, y1c, y18):
    mc.batchwrite_bitunits(["Y1A","Y1C","Y18"], [y1a,y1c,y18])

def run_and_store(label, read_address, memory_coil):
    # First handshake (ignore output)
    first_handshake()
    # Second handshake (read while ON)
    val = second_handshake_read(read_address)
    print(f"{label} read {read_address} value =", val)
    # Store into memory coil
    mc.batchwrite_bitunits([memory_coil], [val])
    print(f"Stored {label} result into {memory_coil}")
    # Explicit reset before next job
    mc.batchwrite_bitunits(["Y1E"], [0])

def drive_lights_by_flags():
    tray_empty = mc.batchread_bitunits("M200",1)[0] == 1
    pass_any = (mc.batchread_bitunits("M300",1)[0] == 1) or (mc.batchread_bitunits("M301",1)[0] == 1)
    fail_any = (mc.batchread_bitunits("M400",1)[0] == 1) or (mc.batchread_bitunits("M401",1)[0] == 1)

    if tray_empty:
        print("Tray Empty → Alarm Y12 ON")
        mc.batchwrite_bitunits(["Y12"], [1]); time.sleep(1); mc.batchwrite_bitunits(["Y12"], [0])
    if pass_any:
        print("PASS → Green Light Y11 ON")
        mc.batchwrite_bitunits(["Y11"], [1]); time.sleep(1); mc.batchwrite_bitunits(["Y11"], [0])
    if fail_any:
        print("FAIL → Red Light Y10 ON")
        mc.batchwrite_bitunits(["Y10"], [1]); time.sleep(1); mc.batchwrite_bitunits(["Y10"], [0])

def reset_for_next_cycle():
    # Ensure handshake is low
    mc.batchwrite_bitunits(["Y1E"], [0])
    # Reset result flags
    mc.batchwrite_bitunits(["M200","M300","M301","M400","M401"], [0,0,0,0,0])
    # Reset memory coils for job results
    mc.batchwrite_bitunits(["M210","M211","M212","M213"], [0,0,0,0])

def main():
    print("Connected to PLC, waiting for M100 to start cycle...")

    while True:
        try:
            if mc.batchread_bitunits("M100",1)[0] == 1:
                print("Start detected → Begin sequence")

                # --- Job1: Tray check ---
                select_job(1,0,0)
                run_and_store("Job1 Tray","X0E","M210")

                if mc.batchread_bitunits("M210",1)[0] == 1:
                    print("Job1 PASS → Tray Empty → M200 ON")
                    mc.batchwrite_bitunits(["M200"], [1])
                else:
                    print("Tray NOT empty → Proceed to Job2")

                    # --- Job2: Color check ---
                    select_job(0,1,0)
                    run_and_store("Job2 Color","X06","M211")

                    if mc.batchread_bitunits("M211",1)[0] == 1:
                        print("Job2 → Orange detected → Proceed to Job3")

                        # --- Job3: Orange pass/fail ---
                        select_job(0,1,1)
                        run_and_store("Job3 Orange","X0E","M212")

                        if mc.batchread_bitunits("M212",1)[0] == 1:
                            print("Job3 PASS → Orange Pass → M300 ON")
                            mc.batchwrite_bitunits(["M300"], [1])
                        else:
                            print("Job3 FAIL → Orange Fail → M400 ON")
                            mc.batchwrite_bitunits(["M400"], [1])

                    else:
                        print("Job2 → Brown detected → Proceed to Job4")

                        # --- Job4: Brown pass/fail ---
                        select_job(1,0,0)  # adjust mapping if needed
                        run_and_store("Job4 Brown","X06","M213")

                        if mc.batchread_bitunits("M213",1)[0] == 1:
                            print("Job4 PASS → Brown Pass → M301 ON")
                            mc.batchwrite_bitunits(["M301"], [1])
                        else:
                            print("Job4 FAIL → Brown Fail → M401 ON")
                            mc.batchwrite_bitunits(["M401"], [1])

                # --- Lights ---
                drive_lights_by_flags()

                # --- Reset start and mark completion ---
                mc.batchwrite_bitunits(["M100"], [0])
                mc.batchwrite_bitunits(["M101"], [1])

                # --- Reset internals for next run ---
                reset_for_next_cycle()

                time.sleep(0.5)
                print("Cycle complete → M101 ON, all flags and M210–M213 cleared, waiting for next M100")

            time.sleep(0.2)

        except Exception as e:
            print("PLC communication error:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
