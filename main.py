# MAIN.PY - Cytron Robo ESP32 BLE Motor Listener

from BLE_CEEO import Listen
import time
import json
from machine import Pin, PWM, I2C, Timer
import neopixel
import vemlsensor

# -------------------------
# BUTTON SETUP
# -------------------------
button_A = Pin(34, Pin.IN)  # Start
button_B = Pin(35, Pin.IN)  # Stop

# -------------------------
# MOTOR SETUP (Robo ESP32: two-input driver)
# -------------------------
M1A = PWM(Pin(12), freq=1000, duty_u16=0)
M1B = PWM(Pin(13), freq=1000, duty_u16=0)
M2A = PWM(Pin(14), freq=1000, duty_u16=0)
M2B = PWM(Pin(27), freq=1000, duty_u16=0)

def set_motor(pa, pb, speed):
    d = int(abs(speed) * 65535 / 100)
    if speed > 0:
        pa.duty_u16(d); pb.duty_u16(0)
    elif speed < 0:
        pa.duty_u16(0); pb.duty_u16(d)
    else:
        pa.duty_u16(0); pb.duty_u16(0)

def drive(left, right):
    left = max(-100, min(100, int(left)))
    right = max(-100, min(100, int(right)))
    set_motor(M1A, M1B, left)
    set_motor(M2A, M2B, right)

def stop():
    drive(0, 0)

stop()


# -------------------------
# KNN color detection
# -------------------------


TARGET = "red"         # the only label we care about
CSV_FILE = "red_samples.csv"
RETRAIN = False        # True = ignore the CSV and retrain from scratch
K_NEIGHBORS = 5
CONFIRM = 2            # consecutive "red" KNN results before LEDs turn on
LED_BRIGHT = 60
LED_HOLD_MS = 600      # keep LEDs lit this long after red was last seen
COLOR_MS = 50          # how often to run the KNN check
DEBUG = False          # True = print every raw KNN label (useful for tuning)

# --- training ---
SAMPLES_PER_SPOT = 20  # readings taken each time you press Enter
SAMPLE_GAP_MS = 50     # >= sensor integration time so readings aren't duplicates
# ----------------------------------------

RED = (LED_BRIGHT, 0, 0)
WHITE = (LED_BRIGHT // 3, LED_BRIGHT // 3, LED_BRIGHT // 3)
OFF = (0, 0, 0)

# ---------------- hardware ----------------
col_i2c = I2C(1, sda=Pin(33), scl=Pin(32), freq=400000)
color_sensor = vemlsensor.VEML6040(col_i2c)
np = neopixel.NeoPixel(Pin(15), 2)


def set_leds(rgb):
    np[0] = rgb
    np[1] = rgb
    np.write()


# ---------------- features ----------------
def features(r, g, b):
    """Chromaticity: each channel's share of the total.
    Ignores overall brightness, so lighting/height changes matter less."""
    s = r + g + b
    if s <= 0:
        return (0.0, 0.0, 0.0)
    return (r / s, g / s, b / s)


# ---------------- CSV ----------------
def load_csv():
    """Return list of (r, g, b, label). Empty list if file missing or blank."""
    rows = []
    try:
        with open(CSV_FILE) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("r,"):   # skip blanks + header
                    continue
                parts = line.split(",")
                if len(parts) != 4:
                    continue
                try:
                    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                except ValueError:
                    continue
                rows.append((r, g, b, parts[3]))
    except OSError:
        pass  # file doesn't exist yet
    return rows


def save_csv(rows):
    with open(CSV_FILE, "w") as f:
        f.write("r,g,b,label\n")
        for r, g, b, label in rows:
            f.write("%d,%d,%d,%s\n" % (r, g, b, label))
    print("Saved %d samples to %s" % (len(rows), CSV_FILE))


# ---------------- training ----------------
def collect(label, rows):
    for _ in range(SAMPLES_PER_SPOT):
        r, g, b, w = color_sensor.read_rgbw()
        rows.append((r, g, b, label))
        time.sleep_ms(SAMPLE_GAP_MS)


def train_group(label, instructions, rows, led):
    print()
    print(instructions)
    spots = 0
    while True:
        cmd = input("  Spot %d: place sensor, press Enter (d = done): " % (spots + 1))
        if cmd.strip().lower() == "d":
            if spots == 0:
                print("  Need at least one spot first.")
                continue
            break
        set_leds(led)          # LEDs on = currently sampling, hold still
        collect(label, rows)
        set_leds(OFF)
        spots += 1
        print("  got %d samples" % SAMPLES_PER_SPOT)


def train():
    print("=== Training red detector ===")
    rows = []
    train_group(TARGET,
                "RED: put the sensor over red patches. Vary position/angle a bit.",
                rows, RED)
    train_group("other",
                "NOT RED: white floor, black tape, green, blue, edges of the tape...\n"
                "  anything the robot might see that should NOT count as red.",
                rows, WHITE)
    save_csv(rows)
    return rows


# ---------------- KNN ----------------
def build_model(rows):
    return [(features(r, g, b), label) for r, g, b, label in rows]


def classify(model, f, k):
    """Majority vote of the k nearest samples: red needs more than half."""
    dists = []
    for (fr, fg, fb), label in model:
        d = (fr - f[0]) ** 2 + (fg - f[1]) ** 2 + (fb - f[2]) ** 2
        dists.append((d, label))
    dists.sort(key=lambda x: x[0])
    nearest = dists[:k]
    red_votes = sum(1 for _, label in nearest if label == TARGET)
    return TARGET if red_votes * 2 > len(nearest) else "other"


def read_label(model):
    r, g, b, w = color_sensor.read_rgbw()
    return classify(model, features(r, g, b), K_NEIGHBORS)

rows = load_csv()      # always read the pre-populated CSV, never train
if rows:
    print("Loaded %d samples from %s" % (len(rows), CSV_FILE))
else:
    print("ERROR: no samples in %s -- red will never be detected" % CSV_FILE)

model = build_model(rows)
n_red = sum(1 for row in rows if row[3] == TARGET)
print("Model: %d red, %d other" % (n_red, len(rows) - n_red))
if n_red == 0 or n_red == len(rows):
    print("WARNING: need both red and not-red samples; set RETRAIN = True")
red_count = 0          # consecutive red readings
last_red_seen = 0      # ticks_ms when red was last confirmed
lit = False


def check_red(t):
    """Runs every COLOR_MS on a timer, so it keeps going while BLE waits/runs."""
    global red_count, last_red_seen, lit
    now_ms = time.ticks_ms()
    label = read_label(model)
    if DEBUG:
        print(label)
    if label == TARGET:
        red_count += 1
    else:
        red_count = 0

    if red_count >= CONFIRM:
        last_red_seen = now_ms
        if not lit:
            lit = True
            set_leds(RED)
            print("Detected red")

    #turn the LEDs off once we've been off red for a moment
    if lit and time.ticks_diff(now_ms, last_red_seen) > LED_HOLD_MS:
        lit = False
        set_leds(OFF)
        print("Red cleared")


color_timer = Timer(0)


# -------------------------
# BLE SETUP
# -------------------------
NAME = "A"
buffer = b""
connected = False

def callback(data):
    global buffer
    if not connected:
        return
    buffer += data
    while b"\n" in buffer:
        line, buffer = buffer.split(b"\n", 1)
        try:
            message = json.loads(line.decode())
            print("Received:", message)
            if "left" in message and "right" in message:
                drive(message["left"], message["right"])
                print("Left:", message["left"], "Right:", message["right"])
        except Exception as e:
            print("Message error:", e)

p = None
print("Robot ready! Motors OFF")

try:
    p = Listen(NAME, verbose=False)
    p.callback = callback

    print("Looking for", NAME, "...")
    if p.connect_up():
        connected = True
        print("Connected")
        count = 0
        while p.is_connected:
            color_timer.init(period=COLOR_MS, mode=Timer.PERIODIC, callback=check_red)
            payload = json.dumps({"from": "listener", "lit": lit}) + "\n"
            for start in range(0, len(payload), 20):
                p.send(payload[start:start + 20])
                time.sleep_ms(50)
            time.sleep(0.3)
    print("Lost connection")
finally:
    color_timer.deinit()
    set_leds(OFF)
    if p:
        stop()
        p.disconnect()


