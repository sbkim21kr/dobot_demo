import csv
import DobotDllType as dType

# --- Connect to Dobot ---
api = dType.load()
state = dType.ConnectDobot(api, "", 115200)[0]
if state != 0:
    print("Failed to connect to Dobot")
    exit()

print("Connected to Dobot!")

# --- Teaching Phase ---
coords = []

while True:
    # Get current pose (Cartesian coordinates)
    pose = dType.GetPose(api)
    x, y, z, r = pose[0], pose[1], pose[2], pose[3]
    print(f"\nPose: X={x:.2f}, Y={y:.2f}, Z={z:.2f}, R={r:.2f}")

    # Ask whether to record or ignore
    choice = input("Record this point? (y=record, i=ignore, q=quit): ").lower()

    if choice == "q":
        break
    elif choice == "y":
        note = input("Enter annotation (optional): ")
        coords.append([x, y, z, r, note])
        print("Waypoint recorded.")
    elif choice == "i":
        print("Ignored.")
    else:
        print("Invalid input, skipped.")

# --- Ask for filename before saving ---
filename = input("\nEnter filename to save (e.g. session1.csv): ").strip()
if not filename.endswith(".csv"):
    filename += ".csv"

# --- Save to CSV ---
with open(filename, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["x","y","z","r","note"])
    writer.writerows(coords)

print(f"\nTeaching data saved to {filename}")
