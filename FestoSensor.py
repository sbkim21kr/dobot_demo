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

def pulse_bit(address, on_time=0.2, off_time=0.2):
    mc.batchwrite_bitunits(headdevice=address, values=[1])
    time.sleep(on_time)
    mc.batchwrite_bitunits(headdevice=address, values=[0])
    time.sleep(off_time)
    print(f"[DEBUG] Pulse {address} → ON {on_time}s, OFF {off_time}s")

def reset_all_y():
    mc.batchwrite_bitunits(headdevice="Y1A", values=[0])
    mc.batchwrite_bitunits(headdevice="Y1C", values=[0])
    mc.batchwrite_bitunits(headdevice="Y18", values=[0])
    mc.batchwrite_bitunits(headdevice="Y1E", values=[0])
    print("[DEBUG] Reset all Y outputs")
    time.sleep(0.2)



def set_job(y1a, y1c, y18):
    if y1a: mc.batchwrite_bitunits(headdevice="Y1A", values=[1])
    if y1c: mc.batchwrite_bitunits(headdevice="Y1C", values=[1])
    if y18: mc.batchwrite_bitunits(headdevice="Y18", values=[1])
    print(f"[DEBUG] Set job → Y1A={y1a}, Y1C={y1c}, Y18={y18}")

def clear_job():
    mc.batchwrite_bitunits(headdevice="Y1A", values=[0])
    mc.batchwrite_bitunits(headdevice="Y1C", values=[0])
    mc.batchwrite_bitunits(headdevice="Y18", values=[0])
    print("[DEBUG] Cleared job bits")
    time.sleep(0.2)

def read_input_bit(address):
    val = mc.batchread_bitunits(headdevice=address, readsize=1)[0]
    ival = int(val)
    print(f"[DEBUG] Read {address} = {ival}")
    return ival

# --- Corrected handshake logic with normal delays ---
def perform_handshake_and_read(input_addr):
    # dummy handshake
    pulse_bit("Y1E", on_time=0.2, off_time=0.2)
    pulse_bit("Y1E", on_time=0.2, off_time=0.2)
    # real handshake: ON, read, then OFF
    mc.batchwrite_bitunits(headdevice="Y1E", values=[1])
    time.sleep(0.5)   # normal settle delay
    val = read_input_bit(input_addr)
    mc.batchwrite_bitunits(headdevice="Y1E", values=[0])
    return val

# --- Job routines ---
def run_job1():
    reset_all_y()
    set_job(1, 0, 0)   # 100
    job1_val = perform_handshake_and_read("X0E")
    clear_job()
    print(f"[DEBUG] Job1 result → {job1_val}")
    return job1_val

def run_dummy_job1():
    reset_all_y()
    set_job(1, 0, 0)   # 100
    perform_handshake_and_read("X0E")
    clear_job()
    

def run_job2():
    reset_all_y()
    set_job(0, 1, 0)   # 010
    job2_val = perform_handshake_and_read("X06")
    clear_job()
    print(f"[DEBUG] Job2 result → {job2_val}")
    return job2_val

def run_job3():
    reset_all_y()
    set_job(1, 1, 0)   # 110
    job3_val = perform_handshake_and_read("X0E")
    clear_job()
    print(f"[DEBUG] Job3 result → {job3_val}")
    return job3_val

def run_job4():
    reset_all_y()
    set_job(0, 0, 1)   # 001
    job4_val = perform_handshake_and_read("X06")
    clear_job()
    print(f"[DEBUG] Job4 result → {job4_val}")
    return job4_val

def main():
    connect_plc()
    reset_all_y()
    print("Connected to PLC, waiting for M100 to start cycle...")

    while True:
        try:
            m100_val = int(mc.batchread_bitunits(headdevice="M100", readsize=1)[0])
            if m100_val == 1:
                print("M100 detected → Begin sequence")
                
                # --- Job1 ---
                job1_val = run_job1()
                if job1_val == 1:
                    print("Outcome 1: Tray Empty M200 is on")
                    mc.batchwrite_bitunits(headdevice="M200", values=[1])
                    pulse_bit("M200")
                    pulse_bit("Y12")   # alarm
                    reset_all_y()
                    print("Cycle complete → M101 will stay OFF")
                    continue

                # --- Job2 ---
                job2_val = run_job2()
                if job2_val == 1:
                    # Orange path
                    job3_val = run_job3()
                    if job3_val == 1:
                        print("Outcome 2: Orange Pass M300 is on")
                        mc.batchwrite_bitunits(headdevice="M300", values=[1])
                        # run_dummy_job1()
                        pulse_bit("M300")
                        pulse_bit("Y11")   # green
                    else:
                        print("Outcome 3: Orange Fail M400 is on")
                        mc.batchwrite_bitunits(headdevice="M400", values=[1])
                        # run_dummy_job1()
                        pulse_bit("M400")
                        pulse_bit("Y10")   # red
                else:
                    # Brown path
                    job4_val = run_job4()
                    if job4_val == 1:
                        print("Outcome 4: Brown Pass M301 is on")
                        mc.batchwrite_bitunits(headdevice="M301", values=[1])
                        # run_dummy_job1()
                        pulse_bit("M301")
                        pulse_bit("Y11")   # green
                    else:
                        print("Outcome 5: Brown Fail M401 is on")
                        mc.batchwrite_bitunits(headdevice="M401", values=[1])
                        # run_dummy_job1()
                        pulse_bit("M401")
                        pulse_bit("Y10")   # red

                reset_all_y()



                print("Cycle complete → M101 will pulse ON and start the next cycle")
                pulse_bit("M101")
                
            else:
                time.sleep(0.5)

        except (ConnectionResetError, socket.error) as e:
            print("PLC communication error (socket):", e)
            try: mc.close()
            except: pass
            time.sleep(1)
            connect_plc()
        except Exception as e:
            print("PLC communication error:", e)
            time.sleep(1)

if __name__ == "__main__":
    main()
