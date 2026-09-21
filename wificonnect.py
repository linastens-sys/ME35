#importing the libraries
import network
import urequests
import time
import mysecrets 
#setting up SSID and password 
''' 
SSID=secrets.SSID
PASSWORD=secrets.PASSWORD
'''
SSID = "tufts_eecs"#"tufts_eecs"
PASSWORD = "foundedin1883" #"foundedin1883"

#function definition 
def connect_wifi():
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("Connected! IP address:", wlan.ifconfig()[0])
    return wlan
 
 #function call
connect_wifi()
 
 #ON REPL you can type wlan.isconnected() hit ENTER. it will return True
 
ISS_URL = "http://api.open-notify.org/iss-now.json"
Cat_URL = "https://time.now/developer/api/timezone/America/New_York"
response = urequests.get(Cat_URL)
data = response.json()
response.close()
# beautify Json
print(data)