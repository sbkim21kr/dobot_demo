import os
import xml.etree.ElementTree as ET
import DobotDllType as dType

# === XML Playback Parser ===
def load_playback_file(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)

    tree = ET.parse(file_path)
    root = tree.getroot()

    points = []
    for i in range(13):  # Adjust if you have more or fewer rows
        row = root.find(f".//row{i}")
        if row is None:
            continue
        try:
            x = float(row.find("item_2").text)
            y = float(row.find("item_3").text)
            z = float(row.find("item_4").text)
            r = float(row.find("item_5").text)
            pause_time = float(row.find("item_10").text)
            gripper_code = int(row.find("item_11").text)

            gripper = "enable" if gripper_code == 2 else "disable"
            points.append((x, y, z, r, pause_time, gripper))
        except Exception as e:
            print(f"Skipping row{i} due to error:", e)

    return points

# === Main Dobot Control ===
def run_dobot_sequence(playback_points):
    if not playback_points:
        print("No valid playback points found. Aborting.")
        return

    api = dType.load()
    state = dType.ConnectDobot(api, "COM4", 115200)[0]
    print("Connection state:", state)

    if state == dType.DobotConnect.DobotConnect_NoError:
        dType.SetQueuedCmdClear(api)

        # Start execution early for faster response
        dType.SetQueuedCmdStartExec(api)

        lastIndex = 0

        for i, (x, y, z, r, pause_time, gripper) in enumerate(playback_points):
            # Move to position
            lastIndex = dType.SetPTPCmd(api,
                                        dType.PTPMode.PTPMOVLXYZMode,
                                        x, y, z, r,
                                        isQueued=1)[0]

            # Gripper control with stabilization delay
            if gripper == "enable":
                dType.SetEndEffectorGripper(api, 1, 1, isQueued=1)
                dType.dSleep(300)  # Wait 300 ms for grip to stabilize
            elif gripper == "disable":
                dType.SetEndEffectorGripper(api, 1, 0, isQueued=1)
                dType.dSleep(300)  # Wait 300 ms for release to complete

            # Optional pause
            if pause_time > 0:
                dType.dSleep(int(pause_time * 1000))

        # Final gripper release (fully disable to stop noise)
        dType.SetEndEffectorGripper(api, 0, 0, isQueued=1)

        # Wait until last command is done
        while lastIndex > dType.GetQueuedCmdCurrentIndex(api)[0]:
            dType.dSleep(100)

        dType.SetQueuedCmdStopExec(api)

        # Final pose
        pose = dType.GetPose(api)
        print("Final coordinates (X, Y, Z, R):", pose[0], pose[1], pose[2], pose[3])

        dType.DisconnectDobot(api)
        print("Finished playback sequence.")
    else:
        print("Failed to connect to Dobot. Check COM port and device status.")

# === Run it ===
if __name__ == "__main__":
    playback_points = load_playback_file("project_1111.playback")
    run_dobot_sequence(playback_points)
