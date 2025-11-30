import xml.etree.ElementTree as ET
import csv
import sys
import os

def load_playback_file(filename):
    """
    Load playback file (XML format).
    Extract waypoints: x, y, z, r, vel, accel, suction/gripper
    """
    try:
        # Check if the file exists
        if not os.path.exists(filename):
            print(f"Error: File not found at '{filename}'")
            return None

        tree = ET.parse(filename)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error: Failed to parse XML file '{filename}'. Details: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading the file: {e}")
        return None

    waypoints = []
    for row in root:
        if row.tag.startswith("row"):  # only process rows like <row0>, <row1>, ...
            try:
                # Extract positional data
                x = float(row.find("item_2").text)
                y = float(row.find("item_3").text)
                z = float(row.find("item_4").text)
                r = float(row.find("item_5").text)
                
                # Extract motion and gripper data
                # Default vel to 50.0 if item_10 is missing
                vel = float(row.find("item_10").text) if row.find("item_10") is not None and row.find("item_10").text else 50.0
                accel = vel # accel is set equal to vel in the original logic
                suction_gripper = int(row.find("item_11").text) if row.find("item_11") is not None and row.find("item_11").text else 0

                wp = (x, y, z, r, vel, accel, suction_gripper)
                waypoints.append(wp)
            except Exception as e:
                print(f"Skipping {row.tag} due to error during data extraction: {e}")
    
    return waypoints

def show_waypoints(waypoints):
    """Prints the extracted waypoints to the console."""
    if not waypoints:
        print("\nNo waypoints to display.")
        return
    
    print("\n--- Extracted Waypoints ---")
    for i, wp in enumerate(waypoints, start=1):
        # Format the output for better readability
        (x, y, z, r, vel, accel, sg) = wp
        print(f"Point{i:03d}: (X:{x:6.2f}, Y:{y:6.2f}, Z:{z:6.2f}, R:{r:6.2f}, Vel:{vel:5.1f}, Accel:{accel:5.1f}, Gripper:{sg})")
    print("---------------------------\n")

def export_to_csv(waypoints, original_filename):
    """Exports the waypoints to a CSV file."""
    if not waypoints:
        print("Cannot export: Waypoints list is empty.")
        return
        
    # Generate CSV filename: replace the extension of the input file with .csv
    base_name = os.path.splitext(original_filename)[0]
    csv_filename = base_name + ".csv"
    
    try:
        with open(csv_filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            # Write header
            csv_writer.writerow(["X", "Y", "Z", "R", "Velocity", "Acceleration", "Suction/Gripper"])
            
            # Write data rows
            csv_writer.writerows(waypoints)
            
        print(f"✅ Successfully exported {len(waypoints)} waypoints to **{csv_filename}**")
        return csv_filename
    except Exception as e:
        print(f"Error writing to CSV file: {e}")
        return None


if __name__ == "__main__":
    
    # 1. Ask the user for the filename
    while True:
        try:
            filename = input("📝 Please enter the XML or .playback filename (e.g., my_path.xml): ").strip()
            if not filename:
                print("Filename cannot be empty. Please try again.")
                continue

            # Ensure the filename has a valid extension if not provided
            if not (filename.lower().endswith(".xml") or filename.lower().endswith(".playback")):
                # Check for a common mistake where the user omits the extension
                if "." not in filename:
                    print("Assuming '.xml' extension.")
                    filename += ".xml"
                else:
                    print("⚠️ Warning: File extension is neither .xml nor .playback. Attempting to load anyway.")

            break
        except EOFError:
            print("\nInput cancelled by user. Exiting.")
            sys.exit(0)
        except Exception as e:
            print(f"An error occurred during input: {e}")
            
    # 2. Load the waypoints from the file
    print(f"\nAttempting to load data from: **{filename}**")
    waypoints = load_playback_file(filename)
    
    if waypoints is not None:
        # 3. Print the coordinates
        show_waypoints(waypoints)
        
        # 4. Export the coordinates to CSV
        export_to_csv(waypoints, filename)