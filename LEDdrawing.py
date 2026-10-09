import time
import math
from machine import Pin, PWM
from LEDpath import points

l1 = 5.5
l2 = 5.5
max_duty = 65535

pwm1 = PWM(Pin(4), freq=50)
pwm2 = PWM(Pin(5), freq=50)

scale = 5 / 12
scaled_points = [
    ((x - 12) * scale, y * scale)
    for x, y in points
]

offset1 = 0
offset2 = 0

i = 0

while i < len(scaled_points):
    x, y = scaled_points[i]

    r = math.sqrt(x**2 + y**2)

    if abs(l1 - l2) <= r <= l1 + l2:
        cos_theta2 = (
            x**2 + y**2 - l1**2 - l2**2
        ) / (2 * l1 * l2)

        cos_theta2 = max(-1, min(1, cos_theta2))

        theta2 = math.acos(cos_theta2)

        theta1 = math.atan2(y, x) - math.atan2(
            l2 * math.sin(theta2),
            l1 + l2 * math.cos(theta2)
        )

        theta1 = math.degrees(theta1)
        theta2 = math.degrees(theta2)

        servo1_angle = theta1 + offset1
        servo2_angle = theta2 + offset2

        # Convert to pulse widths in milliseconds
        pulse1 = 0.5 + servo1_angle / 180 * 2.0
        pulse2 = 0.5 + servo2_angle / 180 * 2.0

        pulse1 = max(0.5, min(2.5, pulse1))
        pulse2 = max(0.5, min(2.5, pulse2))

        pwm1.duty_u16(int(pulse1 * max_duty / 20))
        pwm2.duty_u16(int(pulse2 * max_duty / 20))

        time.sleep(0.05)

    else:
        print("Unreachable point:", x, y)

    i += 1

# One complete sweep finished
pwm1.deinit()
pwm2.deinit()