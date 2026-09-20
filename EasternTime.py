import network
import urequests
import time

from machine import Pin, PWM
from time import ticks_ms, ticks_diff

max_duty = 65535
offset=9

# Servo
pwm = PWM(Pin(4), freq=50)


# Buttons
btn1 = Pin(34, Pin.IN, Pin.PULL_UP)
btn2 = Pin(35, Pin.IN, Pin.PULL_UP)

DEBOUNCE_MS = 200
last_press = 0
#Modes
# Mode 0 = time
# Mode 1 = temperature
# default mode is time
mode = 0

def switch1(pin):
    global last_press
    global mode

    now = ticks_ms()

    if ticks_diff(now, last_press) > DEBOUNCE_MS:

        if pin.value() == 0:
            last_press = now

            # Button 34 -> temperature
            mode = 1

            print("Button 34 pressed")
            print("Temperature mode")


def switch2(pin):
    global last_press
    global mode

    now = ticks_ms()

    if ticks_diff(now, last_press) > DEBOUNCE_MS:

        if pin.value() == 0:
            last_press = now

            # Button 35 -> time
            mode = 0

            print("Button 35 pressed")
            print("Time mode")


btn1.irq(trigger=Pin.IRQ_FALLING, handler=switch1)
btn2.irq(trigger=Pin.IRQ_FALLING, handler=switch2)


def timeposition():
    time_URL = "https://timezones.live/api/v1/time?city=America/New_York"
    time_response = urequests.get(time_URL)
    time_data=time_response.json()
    time_response.close()
    
    current_time=time_data["data"]["currentTime"]
    print(current_time)

    time_part, am_pm = current_time.split()
    hour, minute = map(int, time_part.split(":"))
    

    if am_pm == "AM" and hour ==12:
        print("AM")
        angle12= (minute/720*180)
        angle24= (minute/1440*180)
    elif am_pm == "PM" and hour ==12:
        angle12= (minute/720*180)
        angle24= ((12*60+minute)/1440*180)
    elif am_pm == "PM" and hour != 12:
        angle12= ((60*hour+minute)/720*180)
        angle24= (((12+hour)*60+minute)/1440*180)
    elif am_pm == "AM" and hour != 12:
        angle12= ((60*hour+minute)/720*180)
        angle24= ((hour*60+minute)/1440*180)
        

    #print("24 hour angle:", angle24)
    #print("12 hour angle:",angle12)



    
    # 0.5 to 2.5 are the extremes of the servo
    test_angle=4/12*180
    # we could take out this ratio step if we took out the 180 from theangle calculations, it just helped me develop/ visualize
    angle_ratio=(angle12-offset)/180 # change to angle24 here if you want a 24 hour clock,
    #print(angle_ratio)
    pwm_range=2.5-angle_ratio*2
    #print(pwm_range)
    pos= int(pwm_range*max_duty/20)

    #print(pos)
    return pos



# getting weather api and converting to position
def temppostion():
    weather_URL = "https://api.open-meteo.com/v1/forecast?latitude=42.419331&longitude=-71.119720&current=temperature_2m,rain"
    weather_response = urequests.get(weather_URL)
    weather_data = weather_response.json()
    weather_response.close()

    Rain = weather_data["current"]["rain"]
    Temp = weather_data["current"]["temperature_2m"]
    Temp_f= Temp*9/5+32
    
    print(Temp_f)
    test_temp= -10
    temp_angle=(Temp_f+10)/120*180
    temp_angle_ratio= (temp_angle-offset)/180
    pwm_temp_range=2.5-temp_angle_ratio*2
    temp_pos=int(pwm_temp_range*max_duty/20)
    
    #print(temp_pos)
    return(temp_pos)

      
# while loop    
while True:

    if mode == 0:

        # TIME MODE
        pos = timeposition()
        pwm.duty_u16(pos)
        print(pos)

    elif mode == 1:
    
            
        # TEMPERATURE MODE
        temp_pos = temppostion()
        pwm.duty_u16(temp_pos)

    time.sleep(5)
