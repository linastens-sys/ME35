
import network
import espnow
import neopixel
from machine import Pin
import time

# NeoPixel setup
lights = neopixel.NeoPixel(Pin(15, Pin.OUT), 2)

# ESP-NOW setup
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()

e = espnow.ESPNow()
e.active(True)


def show_color(color):

    color = color.strip().lower()

    if color == "red":
        rgb = (30, 0, 0)

    elif color == "green":
        rgb = (0, 30, 0)

    elif color == "blue":
        rgb = (0, 0, 30)

    else:
        print("Unknown color")
        return

    # Display colour
    for i in range(2):
        lights[i] = rgb

    lights.write()


def lights_off():

    for i in range(2):
        lights[i] = (0, 0, 0)

    lights.write()


# Start with LEDs off
lights_off()

print("Waiting for colour messages...")

while True:

    host, msg = e.recv()

    if msg:
        color = msg.decode().strip().lower()

        print("Received:", color)

        show_color(color)

        time.sleep_ms(500)

        lights_off()
