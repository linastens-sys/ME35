import network
import time
from umqtt.simple import MQTTClient
import ssl
import secrets
import json
from neopixel import NeoPixel
from machine import Pin, PWM, I2C, Timer

M1A = PWM(Pin(12), freq=1000, duty_u16=0)
M1B = PWM(Pin(13), freq=1000, duty_u16=0)
M2A = PWM(Pin(14), freq=1000, duty_u16=0)
M2B = PWM(Pin(27), freq=1000, duty_u16=0)

speed=20

np = NeoPixel(Pin(15), 2)
# Wi-Fi credentials
SSID = secrets.SSID
PASSWORD = secrets.PWD

# MQTT settings
MQTT_BROKER = secrets.mqtt_url 
MQTT_PORT = secrets.port
#MQTT_USERNAME = secrets.mqtt_username 
#MQTT_PASSWORD = secrets.mqtt_password
CLIENT_ID = "esp32_client21"
TOPIC_SUB_Speed = "ME35/speed"
TOPIC_SUB_Direction="ME35/direction"
TOPIC_SUB_LED0= "ME35/led/0"
TOPIC_SUB_LED1= "ME35/led/1"

def set_motor(pa, pb, speed):
    d = int(abs(speed) * 65535 / 100)
    if speed > 0:
        pa.duty_u16(d); pb.duty_u16(0)
    elif speed < 0:
        pa.duty_u16(0); pb.duty_u16(d)
    else:
        pa.duty_u16(0); pb.duty_u16(0)

def stop():
    drive("stop", 0)

def drive(direction="stop",speed=20):
    if direction == "forward":
        M1Dir=-speed
        M2Dir=speed
    elif direction == "backward":
        M1Dir=speed
        M2Dir=-speed
    elif direction == "left":
        M1Dir=speed
        M2Dir=speed
    elif direction == "right":
        M1Dir=-speed
        M2Dir=-speed
    elif direction == "stop":
        M1Dir=0
        M2Dir=0
    else:
        M1Dir=0
        M2Dir=0
    set_motor(M1A, M1B, M1Dir)
    set_motor(M2A, M2B, M2Dir)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
        
    if wlan.isconnected():
        print("WiFi Connected! IP:", wlan.ifconfig()[0])
        return True
    else:
        print("WiFi connection failed!")
        return False

# def light(led):
#             led=led.json()
#             print(led)
#             red= led["r"]
#             green= led["g"]
#             blue= led["b"]
    
def sub_cb(topic, msg):
    print(f"Received message on topic '{topic.decode()}' : '{msg.decode()}'")
    print("topic", topic)
    global speed
    if topic.decode()==TOPIC_SUB_Speed:
            speed= int(msg.decode())
    elif topic.decode()==TOPIC_SUB_Direction:
            print('{msg.decode()}')
            direction= msg.decode()
            print(speed)
            drive(direction, speed)
    elif topic.decode()==TOPIC_SUB_LED0:
            led0= msg.decode()
            led0=json.loads(led0)
            print(led0)
            red0= led0["r"]
            green0= led0["g"]
            blue0= led0["b"]
            np[0] = (red0, green0, blue0)
            np.write()
    elif topic.decode()==TOPIC_SUB_LED1:
            led1=msg.decode()           
            led1=json.loads(led1)
            print(led1)
            red1= led1["r"]
            green1= led1["g"]
            blue1= led1["b"]
            np[1] = (red1, green1, blue1)
            np.write()
def mqtt_connect():
    try:
        client = MQTTClient(
            client_id=CLIENT_ID,
            server=MQTT_BROKER,
            port=MQTT_PORT,
            #user=MQTT_USERNAME,
            #password=MQTT_PASSWORD,
            #ssl=True,  # Enable SSL
            ssl_params={'server_hostname': MQTT_BROKER}  # Important for certificate validation
        )
        client.set_callback(sub_cb)
        client.connect()
        np[0] = (0, 0, 0)
        np[1] = (0, 0, 0)
        np.write()
        client.subscribe(TOPIC_SUB_Speed)
        client.subscribe(TOPIC_SUB_Direction)
        client.subscribe(TOPIC_SUB_LED0)
        client.subscribe(TOPIC_SUB_LED1)# change this to the topic you want to subscribe
        print("MQTT Connected successfully!")
        return client
    except OSError as e:
        while True:
            print(f"MQTT Connection failed: {e}")
            np[0] = (255, 0, 0)
            np[1] = (255, 0, 0)
            np.write()
            time.sleep(0.4)
            np[0] = (0, 0, 0)
            np[1] = (0, 0, 0)
            np.write()
            time.sleep(0.4)
            stop()
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if connect_wifi():
    client = mqtt_connect()
    if client:
        while True:
            try:
                client.check_msg()
                time.sleep(1)
            except Exception as e:
                print(f"Checking message failed: {e}")
                np[0] = (255, 0, 0)
                np[1] = (255, 0, 0)
                np.write()
                time.sleep(0.4)
                np[0] = (0, 0, 0)
                np[1] = (0, 0, 0)
                np.write()
                time.sleep(0.4)
                stop()


        
            
          
