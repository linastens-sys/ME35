from machine import Pin, ADC
import neopixel #importing the library
import time
import light_knn
import random
from machine import ADC, Pin
from machine import Pin, I2C
import machine

lights = neopixel.NeoPixel(Pin(15),2) # 15 is the Pin for neopixel and 2 is the number of lights
lights[0] = (0,0,0)
lights[1] = (0,0,0)
lights.write()
red= (1000,0,0)
green = (0,1000,0)
off =(0,0,0)

# 1. Setup the PWM pin for the servo (adjust Pin 15 to your actual physical pin)
servo_pin = machine.Pin(4)
pwm = machine.PWM(servo_pin)
pwm.freq(50)  # Standard 50Hz frequency for servos

# 2. Define your extremes (duty cycle values for 16-bit u16)

# Adjust these values based on your specific servo's physical range.
YES = 1638  # Extreme 1 (e.g., 0 degrees)
NO = 8192   # Extreme 2 (e.g., 180 degrees)
CENTER = 4915 # Midpoint for the indecisive wobble

numbers = [1, 2] # define numbers for good(1) and bad(2) fortunes 
sensor = ADC(Pin(25))
sensor.atten(ADC.ATTN_11DB)


i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)

ADDR = 0x19

# Verify sensor
who = i2c.readfrom_mem(ADDR, 0x0F, 1)[0]
print("Sensor ID:", hex(who))

if who != 0x33:
    raise Exception("Unexpected sensor ID")

# Enable X, Y, Z at 100 Hz
i2c.writeto_mem(ADDR, 0x20, b'\x57')

# High-resolution mode, +/- 2g
i2c.writeto_mem(ADDR, 0x23, b'\x08')

time.sleep_ms(100)

def read_acceleration():
    data = i2c.readfrom_mem(ADDR, 0xA8, 6)

    values = []

    for i in range(0, 6, 2):
        raw = data[i] | (data[i + 1] << 8)

        if raw >= 32768:
            raw -= 65536

        raw = raw >> 4
        values.append(raw / 1000)

    return values[0], values[1], values[2]


# Tail-pull detection
NICE_THRESHOLD = 0.15
MEAN_THRESHOLD = 0.45# g; tune after testing
COOLDOWN_MS = 5000

prev_x, prev_y, prev_z = read_acceleration()
last_trigger = time.ticks_ms()

# define decisive servo movement
def servo_decisive(fortune):
    time.sleep(0.3)
    if fortune == 1:
        pwm.duty_u16(YES)
        lights[0]= green
        lights[1]= green
        lights.write()
    elif fortune == 2:
        pwm.duty_u16(NO)
        lights[0]= red
        lights[1]= red
        lights.write()
    time.sleep(3)    
    pwm.duty_u16(CENTER)
    lights[0]= off
    lights[1]= off
    lights.write()
    
    
    # Allow the physical motor time to actually reach the position
    time.sleep(0.5) 
def servo_indecisive(fortune):
    # 1. Start at center position
    pwm.duty_u16(CENTER)
    time.sleep(0.3)
    
    # 2. Wobble back and forth 3 times to look indecisive
    # We use slightly softer extremes so it looks like a rapid "shaking" effect
    wobble_low = int(CENTER - (CENTER - YES) * 0.6)   # 60% towards YES
    wobble_high = int(CENTER + (NO - CENTER) * 0.6)   # 60% towards NO
    
    for _ in range(3):
        pwm.duty_u16(wobble_low)
        time.sleep(0.15)  # Fast back-and-forth pacing
        pwm.duty_u16(wobble_high)
        time.sleep(0.15)
        
    # 3. Return to center briefly for dramatic effect
    pwm.duty_u16(CENTER)
    time.sleep(0.4)
    
    # 4. Make the final decision
    servo_decisive(fortune)




# Load saved data, or calibrate if necessary
if not light_knn.load_data():
    light_knn.collect_data(sensor)

    
# Read and classify continuously
while True:
    reading = sensor.read()
    result = light_knn.k_nearest_neighbor(reading)

    #print("Reading:", reading, "Classification:", result)

    x, y, z = read_acceleration()
    

    # Total change since the previous reading
    change = (
         z - prev_z
    )

    now = time.ticks_ms()

    if (change > NICE_THRESHOLD and change < MEAN_THRESHOLD and
        time.ticks_diff(now, last_trigger) > COOLDOWN_MS) and result== "dark":
        print("unfair")
        probability = [0.9, 0.1]
        last_trigger = now
        if random.random() < probability[0]:
            fortune = numbers[0]
        else:
            fortune = numbers[1]
        servo_decisive(fortune)
    elif (change > NICE_THRESHOLD and change < MEAN_THRESHOLD and
            time.ticks_diff(now, last_trigger) > COOLDOWN_MS) and result== "light":
        print("fair")
        probability = [0.5, 0.5]
        last_trigger = now
        if random.random() < probability[0]:
            fortune = numbers[0]
        else:
            fortune = numbers[1]
        servo_decisive(fortune)
    elif ( change > MEAN_THRESHOLD and
            time.ticks_diff(now, last_trigger) > COOLDOWN_MS) and result == "dark":
        print("tricky and unfair")
        probability = [0.9, 0.1]
        last_trigger = now
        if random.random() < probability[0]:
            fortune = numbers[0]
        else:
            fortune = numbers[1]
        
        servo_indecisive(fortune)
    elif ( change > MEAN_THRESHOLD and
            time.ticks_diff(now, last_trigger) > COOLDOWN_MS) and result == "light":
        print("tricky but fair")
        probability = [0.5, 0.5]
        last_trigger = now
        if random.random() < probability[0]:
            fortune = numbers[0]
        else:
            fortune = numbers[1]
        servo_indecisive(fortune)
        
    prev_x, prev_y, prev_z = x, y, z

    time.sleep_ms(100)