import os
import pycom
import utime
from machine import SD


def check(path):

    #test sd object creation

    try:
        sd = SD()
    except:
        pycom.rgbled(0xff0000)  #vermelho
        print('sd error')
        #sd.deinit()
        sd = SD()
    #test mounting

    try:
        os.mount(sd, path)
    except:
        pycom.rgbled(0xff0000)  #vermelho
        print('already mounted')

    utime.sleep(5)
