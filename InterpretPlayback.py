import xml.etree.ElementTree as ET

def load_playback_file(filename):
    """
    Load playback file (XML format).
    Extract waypoints: x, y, z, r, vel, accel, suction/gripper
    """
    tree = ET.parse(filename)
    root = tree.getroot()

    waypoints = []
    for row in root:
        if row.tag.startswith("row"):  # only process rows like <row0>, <row1>, ...
            try:
                x = float(row.find("item_2").text)
                y = float(row.find("item_3").text)
                z = float(row.find("item_4").text)
                r = float(row.find("item_5").text)
                vel = float(row.find("item_10").text) if row.find("item_10") is not None else 50.0
                accel = vel
                suction_gripper = int(row.find("item_11").text)

                wp = (x, y, z, r, vel, accel, suction_gripper)
                waypoints.append(wp)
            except Exception as e:
                print(f"Skipping {row.tag} due to error: {e}")
    return waypoints

def show_waypoints(waypoints):
    for i, wp in enumerate(waypoints, start=1):
        print(f"Point{i} : {wp}")

if __name__ == "__main__":
    filename = "playback.xml"  # make sure this file is in the same folder
    waypoints = load_playback_file(filename)
    show_waypoints(waypoints)
