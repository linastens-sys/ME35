
from machine import Pin, SoftI2C
import time
import math


from machine import Pin, PWM
from time import ticks_ms, ticks_diff

max_duty = 65535
offset=0

# Servo
pwm1 = PWM(Pin(4), freq=50)
pwm2 = PWM(Pin(5), freq=50)

button_Play = Pin(34, Pin.IN, Pin.PULL_UP)
button_Train = Pin(35, Pin.IN, Pin.PULL_UP)

i2c = SoftI2C(scl = Pin(22), sda = Pin(21))

print(i2c.scan())
import time


DEBOUNCE_MS = 200
last_press = 0

pressed_flag = False
STATE_PLAY = False
STATE_TRAIN = True

def playButton(p):
    global STATE_PLAY
    global STATE_TRAIN
    STATE_PLAY = True
    STATE_TRAIN = False


def trainButton(p):
    global pressed_flag
    global STATE_TRAIN
    STATE_TRAIN = True
    pressed_flag = True

    
button_Train.irq(trigger=Pin.IRQ_RISING, handler=trainButton)
button_Play.irq(trigger=Pin.IRQ_RISING, handler=playButton)



import veml6040
sensor = veml6040.VEML6040(i2c)

sensor.trigger_measurement()
   
def k_nearest_neighbor(r,g,b, k =1):
    distances = []
    for index, d in enumerate(data):
        dist = math.sqrt((r-d[0])**2+(g-d[1])**2+(b-d[2])**2)
        distances.append([dist,d[3]])
    
    distances.sort()
    distances = distances[:k] #get k distances
    classes = []
    for dist in distances:
        classes.append(dist[1])
    print("k classes", classes)
    most_number_of_closest_classes = max(set(classes), key = classes.count)
    print("max classes ", most_number_of_closest_classes)
    
    return most_number_of_closest_classes


def setservo(sensed_color):
    pwm1.duty_u16(int(1.5 * max_duty / 20))
    pwm2.duty_u16(int(1.5 * max_duty / 20))
    
    if sensed_color == "red":
        pos = int(2.5 * max_duty / 20)
        pwm1.duty_u16(pos)
        time.sleep(3)
        pwm1.duty_u16(int(1.5 * max_duty / 20))

    elif sensed_color == "blue":
        pos = int(0.5 * max_duty / 20)
        pwm1.duty_u16(pos)
        time.sleep(3)
        pwm1.duty_u16(int(1.5 * max_duty / 20))

    elif sensed_color == "green":
        pos = int(2.5 * max_duty / 20)
        pwm2.duty_u16(pos)
        time.sleep(3)
        pwm2.duty_u16(int(1.5 * max_duty / 20))

    elif sensed_color == "no clue":
        pos = int(0.5 * max_duty / 20)
        pwm2.duty_u16(pos)       
        time.sleep(3)
        pwm2.duty_u16(int(1.5 * max_duty / 20))
        
data = []
color = ""
index = 0

while True:
    red, green, blue, white = sensor.read_rgbw()
    if(STATE_TRAIN and pressed_flag):
        #print(red, green, blue, white)
        index = index+1
        if index <= 5:
            color = "red"
        elif index >5 and index<=10:
            color = "blue"
        elif index >10 and index<=15:
            color = "green"
        else:
            color = "no clue"
        data.append((red/white, green/white, blue/white, color))
        print(data)
        pressed_flag = False
           
    if(STATE_PLAY):
        what_class = k_nearest_neighbor(red/white, green/white, blue/white, 1)
        print(what_class)
        time.sleep(0.1)
        setservo(what_class)
        
        
        STATE_PLAY = False
    time.sleep(0.1)