import encoder
import time
import network
import urequests
import ubinascii
import mysecrets
import math


WIFI_SSID = mysecrets.SSID
WIFI_PASS = mysecrets.PWD

ACCESS_KEY = mysecrets.OS_A2
SECRET_KEY = mysecrets.OS_S2

DID = "8fc929adacefe8180b9633d1"
WID = "41f2efbb9f94fd1a20e944c6"
EID = "d82f45c883dbe54c46cebce4"



enc1 = encoder.Count(32, 39)
enc2 = encoder.Count(25, 33)

last1 = enc1.value()
last2 = enc2.value()

count1 = 0
count2 = 0

MAX_COUNT1 = 1000
MAX_COUNT2 = 1000


def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)

    if not wifi.isconnected():
        wifi.connect(WIFI_SSID, WIFI_PASS)

        while not wifi.isconnected():
            time.sleep(0.5)

    print("Connected")



def get_headers():
    creds = ubinascii.b2a_base64(
        (ACCESS_KEY + ":" + SECRET_KEY).encode()
    ).decode().strip()

    return {
        "Authorization": "Basic " + creds,
        "Accept": "application/json;charset=UTF-8;qs=0.09",
        "Content-Type": "application/json;charset=UTF-8"
    }



def set_onshape_angles(angle1_deg, angle2_deg):

    url = "https://cad.onshape.com/api/v16/assemblies/d/{}/w/{}/e/{}/matevalues".format(
        DID, WID, EID
    )

    body = {
        "mateValues": [

            {
                "mateName": "Cylindrical 3",
                "rotationZ": math.radians(angle1_deg),
                "translationZ": -0.00349999984,
                "jsonType": "Cylindrical",
                "featureId": "MDJmWuCzuyDD+CAQM",
                "ownerOccurrencePath": []
            },

            {
                "mateName": "Cylindrical 5",
                "rotationZ": math.radians(angle2_deg),
                "translationZ": 0.02695,
                "jsonType": "Cylindrical",
                "featureId": "MfE5+Knql1sWi3Aqe",
                "ownerOccurrencePath": []
            }
        ]
    }

    response = urequests.post(
        url,
        headers=get_headers(),
        json=body
    )

    print("POST status:", response.status_code)

    if response.status_code != 200:
        print(response.text)

    response.close()



connect_wifi()

last_sent_angle1 = None
last_sent_angle2 = None



while True:

    value1 = enc1.value()
    value2 = enc2.value()

    # Update encoder counts
    count1 = count1 + (value1 - last1)
    count2 = count2 + (value2 - last2)

    last1 = value1
    last2 = value2


    if count1 > MAX_COUNT1:
        count1 = MAX_COUNT1
        print("MOTOR 1 MAX ANGLE REACHED")

    if count1 < -MAX_COUNT1:
        count1 = -MAX_COUNT1
        print("MOTOR 1 MIN ANGLE REACHED")


    if count2 > MAX_COUNT2:
        count2 = MAX_COUNT2
        print("MOTOR 2 MAX ANGLE REACHED")

    if count2 < -MAX_COUNT2:
        count2 = -MAX_COUNT2
        print("MOTOR 2 MIN ANGLE REACHED")


    angle1 = count1 / MAX_COUNT1 * 90
    angle2 = count2 / MAX_COUNT2 * 90


    print("Encoder 1:", count1)
    print("Angle 1:", angle1)

    print("Encoder 2:", count2)
    print("Angle 2:", angle2)


    motor1_changed = (
        last_sent_angle1 is None
        or abs(angle1 - last_sent_angle1) >= 1
    )

    motor2_changed = (
        last_sent_angle2 is None
        or abs(angle2 - last_sent_angle2) >= 1
    )


    if motor1_changed or motor2_changed:

        set_onshape_angles(angle1, angle2)

        last_sent_angle1 = angle1
        last_sent_angle2 = angle2


    time.sleep(0.5)
