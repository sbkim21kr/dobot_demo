import time
import socket
import pymcprotocol
import sys

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

def main():
    connect_plc()

    # Ask user which device to pulse
    address = input("Enter the device to pulse (e.g. M100): ").strip()

    # Read the device before pulsing
    val = int(mc.batchread_bitunits(headdevice=address, readsize=1)[0])
    print(f"[DEBUG] Current value of {address} = {val}")

    # Only pulse if the device is OFF (0)
    if val == 0:
        pulse_bit(address, on_time=0.2, off_time=0.2)
        print(f"[INFO] Finished pulsing {address}. Exiting now...")
        sys.exit(0)
    else:
        print(f"[INFO] {address} is already ON (value={val}). No pulse performed. Exiting now...")
        sys.exit(0)

if __name__ == "__main__":
    main()
