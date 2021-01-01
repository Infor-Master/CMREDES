#!/usr/bin/env python
#
# Copyright (c) 2019, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
#

""" OTAA Node example compatible with the LoPy Nano Gateway """

from network import LoRa
import socket
import binascii
import struct
import time
import utime
import config
import machine
import json

import SDmount
from MQ131_O3_Sensor import MQ131
from MiCs6814_MultiChannel_Sensor import MiCS6814
from SEN0219_CO2_Sensor import SEN0219
from SEN0219_CO2_Sensor import SEN0219_SERIAL
from PMS5003ST_Sensor import PMS5003ST

# initialize LoRa in LORAWAN mode.
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

# create an OTA authentication params
dev_eui = binascii.unhexlify('007E50A0D44B3959')
app_eui = binascii.unhexlify('70B3D57ED003AC17')
app_key = binascii.unhexlify('988FB2650ACDB14C5F83E5669B6DA256')

# set the 3 default channels to the same frequency (must be before sending the OTAA join request)
lora.add_channel(0, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
lora.add_channel(1, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
lora.add_channel(2, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)

# join a network using OTAA
lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=0, dr=config.LORA_NODE_DR)

# wait until the module has joined the network
print('Waiting for LoRaWAN network connection...')
while not lora.has_joined():
    utime.sleep(1)
    if utime.time() > 60:
        print("possible timeout or collision")
        machine.reset()
    pass

print('Network joined!')

# remove all the non-default channels
for i in range(3, 16):
    lora.remove_channel(i)

# create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# set the LoRaWAN data rate
s.setsockopt(socket.SOL_LORA, socket.SO_DR, config.LORA_NODE_DR)

# make the socket non-blocking
s.setblocking(False)

def read_sensors():
    try:
        MiCS = MiCS6814(SDA='P10', SCL='P11')
        MiCSgases = MiCS.calcAllGases()
        MiCS.deinit()
        NO2=str(MiCSgases[1])

        MQ = MQ131(pin='P18', R0=1393)
        MQvolts = MQ.MQRead()
        MQPPB = MQ.MQGet_PPB(MQvolts)
        O3 = str(MQPPB)

        PMS = PMS5003ST(TX='P3', RX='P21')
        PMSdata = PMS.PMSReadActive()
        PMS.deinit()
        CH2O_PPM=(24.45 * PMSdata[12]) / 30.026
        CH2O=str(CH2O_PPM)
        Temp=str(PMSdata[13])
        Humd=str(PMSdata[14])

        SEN_S = SEN0219_SERIAL(TX='P22', RX='P23')
        SENdata = SEN_S.SEN_Serial_read()
        SEN_S.deinit()
        SENPPM = (256*SENdata[2]) + SENdata[3]
        CO2=str(SENPPM)

        jsn = {
            "NO2": NO2,
            "O3": O3,
            "CO2": CO2,
            "CH2O": CH2O,
            "Temp": Temp,
            "Humd": Humd
        }
        return json.dumps(jsn)

    except Exception as e:
        import sys
        print("exception")
        with open("error.log", "a") as f:
            sys.print_exception(e, f)

def send_messages():

    print("Sending data")
    uplink_message = read_sensors()
    #uplink_message = '{"pressure": 12, "time": '+str(utime.time())+'}'

    if (uplink_message != None):
        print("Package: "+str(uplink_message))
        s.send(uplink_message)


def check_downlink_messages():

    downlink_message, port = s.recvfrom(256) # See if a downlink message arrived

    if not downlink_message: # If there was no message, get out now
        return

    print("Downlink message received!")
    print(downlink_message)
    print(port)

    p_relay = pin('9', mode=Pin.OUT, pull=Pin.PULL_UP)

    if downlink_message[0]: # The first byte is non-zero
        print("Relay OFF")
        p_relay.PULL_DOWN
    else:
        print("Relay ON")
        p_relay.PULL_UP

while lora.has_joined():
    send_messages()
    for i in range(20):
        check_downlink_messages()
        time.sleep(1)
