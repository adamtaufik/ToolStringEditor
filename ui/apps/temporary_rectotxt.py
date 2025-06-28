

# python temporary_rectotxt.py input.rec output.txt


import sys
from datetime import datetime, timedelta


def convert_rec_to_txt(input_file, output_file):
    # Read .rec file
    with open(input_file, 'r') as f:
        lines = f.readlines()

    # Extract header information
    timestamp_days = None
    serial_no = None
    calibration = None

    for line in lines:
        if "Time stamp:" in line:
            timestamp_days = float(line.split(':')[1].strip())
        elif "Tool Serial No." in line:
            serial_no = line.split(':')[1].strip()
        elif "Calibration:" in line:
            calibration = line.split(':')[1].strip()
        if timestamp_days is not None and serial_no is not None and calibration is not None:
            break

    if timestamp_days is None or serial_no is None:
        raise ValueError("Required header information not found in .rec file")

    # Calculate base datetime (1/1/0001 + timestamp days)
    base_datetime = datetime(1, 1, 1) + timedelta(days=timestamp_days)

    # Parse data points
    data_points = []
    for line in lines:
        stripped = line.strip()
        if not stripped or any(keyword in stripped for keyword in
                               ["Time stamp", "Tool Serial No.", "Calibration",
                                "Data Units", "Gauge Range"]):
            continue

        parts = stripped.split()
        if len(parts) < 3:
            continue
        try:
            hours = float(parts[0])
            pressure = float(parts[1])
            temp = float(parts[2])
            data_points.append((hours, pressure, temp))
        except ValueError:
            continue

    # Write .txt file
    with open(output_file, 'w') as f:
        # Write header fields
        f.write("Reservoir      : \n")
        f.write("Field/Pool     : \n")
        f.write("Well Location  : \n")
        f.write("Well Name      : \n")
        f.write("Formation Name : \n")
        f.write("Client Name    : \n")
        f.write("Test Name      : \n")
        f.write(f"Gauge S/N      : {serial_no}\n")
        f.write(f"Calibration    : {calibration}\n\n")

        # Write table header
        f.write('       Date       Time     Press     Temp        "Event"\n')
        f.write(' dd-mm-yyyy hh:mm:ss psia      degF\n')

        # Write data rows
        for hours, pressure, temp in data_points:
            elapsed_seconds = hours * 3600
            current_dt = base_datetime + timedelta(seconds=elapsed_seconds)
            date_str = current_dt.strftime("%d/%m/%Y")
            time_str = current_dt.strftime("%H:%M:%S")
            press_str = f"{pressure:.3f}"
            temp_str = f"{temp:.3f}"
            f.write(f"{date_str} {time_str} {press_str}    {temp_str}          \n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python rec2txt.py <input.rec> <output.txt>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    convert_rec_to_txt(input_file, output_file)
    print(f"Converted {input_file} to {output_file}")