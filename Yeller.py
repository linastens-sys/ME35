       # Yeller (peripheral)

from BLE_CEEO import Yell
import time
import json
import machine
from machine import Pin, PWM
import math
xPin=33
yPin=32
xStick=machine.ADC(xPin)
yStick=machine.ADC(yPin)

def scale_motor(left, right):
    MAX_INPUT = 17500
    MAX_OUTPUT = 100

    left = int(left / MAX_INPUT * MAX_OUTPUT)
    right = int(right / MAX_INPUT * MAX_OUTPUT)

    left = max(-MAX_OUTPUT, min(MAX_OUTPUT, left))
    right = max(-MAX_OUTPUT, min(MAX_OUTPUT, right))
    #print(left, right)

    return left/2, right/2


NAME = "A"
buffer = b""

import neopixel #importing the library

lights = neopixel.NeoPixel(Pin(15),2) # 0 is the Pin for neopixel and 4 is the number of lights
lights[0] = (0,0,0)
lights[1] = (0,0,0)# set the color of 0th light to purple 
lights.write()

BUZZER_PIN = 23
buzzer = PWM(Pin(BUZZER_PIN), freq=2000)
buzzer.duty_u16(0)

demo_requested = False

def tone(freq, ms, gap_ms=20):
        if freq > 0:
            buzzer.freq(int(freq))
            buzzer.duty_u16(20000)
        time.sleep_ms(ms)
        buzzer.duty_u16(0)
        time.sleep_ms(gap_ms)


def demo(np):
    n = np.n
    for f, ms in ((392, 150), (523, 150), (659, 150), (784, 300),
                  (659, 150), (784, 600)):
        tone(f, ms, 30)

    # cycle
    for i in range(4 * n):
        for j in range(n):
            np[j] = (0, 0, 0)
        np[i % n] = (255, 255, 255)
        np.write()
        time.sleep_ms(25)

    # bounce
    for i in range(4 * n):
        for j in range(n):
            np[j] = (0, 0, 128)
        if (i // n) % 2 == 0:
            np[i % n] = (0, 0, 0)
        else:
            np[n - 1 - (i % n)] = (0, 0, 0)
        np.write()
        time.sleep_ms(60)

    # fade in/out
    for i in range(0, 4 * 256, 8):
        for j in range(n):
            if (i // 256) % 2 == 0:
                val = i & 0xff
            else:
                val = 255 - (i & 0xff)
            np[j] = (val, 0, 0)
        np.write()

    # clear
    for i in range(n):
        np[i] = (0, 0, 0)
        np.write()
    


def callback(data):
    # Pieces arrive in up to 20-byte chunks; a newline ends each message
    global buffer, demo_requested
    buffer += data
    while b"\n" in buffer:
        line, buffer = buffer.split(b"\n", 1)
        message= json.loads(line.decode())
        print(message)
        if message.get("lit") is True:
            demo_requested = True
        


p = None
try:
    
    p = Yell(NAME, interval_us=30000, verbose=False)
    p.callback = callback

    print("Waiting for a listener...")
    if p.connect_up():
        print("Connected")
        count = 0
        while p.is_connected:
            if demo_requested:
                demo_requested = False
                demo(lights)
           
            yVal=xStick.read_u16()
            xVal=yStick.read_u16()

            #time.sleep(0.3)
            
            L=yVal-xVal-100
            R= yVal+xVal-64000
    
            left_pwm, right_pwm = scale_motor(L, R)
            

            payload = json.dumps({"from": "yeller", "left": left_pwm, "right": right_pwm}) + "\n"

            # Send in 20-byte pieces (the default packet size)
            for start in range(0, len(payload), 20):
                p.send(payload[start:start + 20])
                time.sleep_ms(30)
            time.sleep(0.3)
            
    print("Lost connection")
finally:
    if p:
        print("fail")
        p.disconnect()
