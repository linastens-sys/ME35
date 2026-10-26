
import time

DATA_FILE = "light_data.txt"
data = []


def collect_data(sensor):
    global data
    data = []

    print("Expose sensor to LIGHT.")
    time.sleep(2)

    # Collect 5 light samples
    for i in range(5):
        reading = sensor.read()
        data.append([reading, "light"])
        print("Light sample", i + 1, ":", reading)
        time.sleep(1)

    print("Light samples complete.")
    print("Cover the sensor to make it DARK.")
    time.sleep(10)

    # Collect 5 dark samples
    for i in range(5):
        reading = sensor.read()
        data.append([reading, "dark"])
        print("Dark sample", i + 1, ":", reading)
        time.sleep(1)

    save_data()


def save_data():
    with open(DATA_FILE, "w") as f:
        for reading, label in data:
            f.write(str(reading) + "," + label + "\n")

    print("Calibration saved to", DATA_FILE)


def load_data():
    global data
    data = []

    try:
        with open(DATA_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 2:
                    data.append([int(parts[0]), parts[1]])

        if len(data) == 10:
            print("Loaded saved calibration.")
            return True

        print("Calibration file is incomplete.")
        data = []
        return False

    except OSError:
        print("No saved calibration found.")
        return False


def k_nearest_neighbor(light, k=3):
    if not data:
        return None

    distances = []

    for d in data:
        dist = abs(light - d[0])
        distances.append([dist, d[1]])

    distances.sort()
    classes = [item[1] for item in distances[:k]]

    return max(set(classes), key=classes.count)
