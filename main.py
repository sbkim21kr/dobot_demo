# main.py
import time
import pymcprotocol

from DobotControl_COM3 import run_dobot_com3
from DobotControl_COM4 import run_dobot_com4
from DobotControl_COM5 import run_dobot_com5

# PLC settings
PLC_IP = "192.168.10.100"
PLC_PORT = 5051

# Per-robot signals
R1_START = "D100"; R1_END = "D101"   # COM3
R2_START = "D110"; R2_END = "D111"   # COM4
R3_START = "D120"; R3_END = "D121"   # COM5

def read_word(plc, device):
    data = plc.batchread_wordunits(headdevice=device, readsize=1)
    return data[0] if isinstance(data, (list, tuple)) and data else data

def handle_robot(plc, start_dev, end_dev, runner, label):
    start_val = read_word(plc, start_dev)
    if start_val == 1:
        print(f"[{label}] Start detected at {start_dev}. Running motion.")
        runner()
        plc.batchwrite_wordunits(headdevice=end_dev, values=[1])
        plc.batchwrite_wordunits(headdevice=start_dev, values=[0])
        print(f"[{label}] End set at {end_dev}; {start_dev} reset to 0.")

def mes_cycle_event_loop():
    plc = pymcprotocol.Type3E()
    plc.connect(PLC_IP, PLC_PORT)
    print(f"PLC connected to {PLC_IP}:{PLC_PORT}")

    try:
        while True:
            # Check each robot’s start signal
            handle_robot(plc, R1_START, R1_END, run_dobot_com3, "COM3")
            handle_robot(plc, R2_START, R2_END, run_dobot_com4, "COM4")
            handle_robot(plc, R3_START, R3_END, run_dobot_com5, "COM5")

            # Polling interval: 50 ms
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("Stopping loop by user request.")
    finally:
        plc.close()
        print("PLC connection closed.")

if __name__ == "__main__":
    mes_cycle_event_loop()
