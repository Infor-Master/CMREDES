from time import sleep
from machine import ADC
from machine import UART
import utime

class SEN0219:
    #Sensor datasheet has a graphical representation of ppm of gas by V in a linear function. By using the graphical funcion one can obtain the gas density in ppm
    #2 points of the gas function are used to find the slope of the linear function (2V at 5000ppm) and (0.4 at 0ppm)
    #To Calibrate the Sensor by Hardware, one should place it in a CO2 free enviroment and then wire to ground both pin 8 and 20 of the Sensor for 7 seconds
    #To Calibrate the Sensor by Software, one should place it in a enviroment close to average CO2 (400ppm), measure the voltage output, and use that value as R0
    READ_SAMPLE_INTERVAL = const(500)
    READ_SAMPLE_TIMES = const(10)

    def __init__(self, pin, offset):
        self.pin = pin
        self.offset = offset
        self.adc = ADC(bits=12)
        self.apin = self.adc.channel(pin=self.pin, attn=ADC.ATTN_11DB)

    def deinit(self):
        self.apin.deinit()
        self.adc.deinit()

    def SENRead(self):
        v=float(0)
        for i in range(READ_SAMPLE_TIMES):
            v += self.apin()
            sleep(READ_SAMPLE_INTERVAL/1000)
        return ((v/READ_SAMPLE_TIMES)*3.3/4096)   #3.3v - ATTN_11DB & 4096 - 12bits

    def SENCalibrate_offset(self, volts):
        # 0,528V -> 400 ppm
        if (volts<=0.528):
            return 0
        offset = (((volts-0.4)*5000)/1.6) - 400
        return offset

    def SENGet_PPM(self, volts):
        if (volts<=0.4):
            return False
        ppm=(((volts-0.4)*5000)/1.6)-self.offset   #0.4 = Zero & (5000-0)/(2-0.4) = Linear Function
        return ppm

class SEN0219_SERIAL:

    # byte mhzCmdReadPPM[9] = {0xFF,0x01,0x86,0x00,0x00,0x00,0x00,0x00,0x79};
    # byte mhzResp[9];    // 9 bytes bytes response
    # byte mhzCmdCalibrateZero[9] = {0xFF,0x01,0x87,0x00,0x00,0x00,0x00,0x00,0x78};
    # byte mhzCmdABCEnable[9] = {0xFF,0x01,0x79,0xA0,0x00,0x00,0x00,0x00,0xE6};
    # byte mhzCmdABCDisable[9] = {0xFF,0x01,0x79,0x00,0x00,0x00,0x00,0x00,0x86};
    # byte mhzCmdReset[9] = {0xFF,0x01,0x8d,0x00,0x00,0x00,0x00,0x00,0x72};

    def __init__(self, TX, RX):
        self.uart = UART(1, 9600, bits=8, parity=None, stop=1, pins=(TX,RX))
        #self.uart.write(b'\xFF\x01\x8D\x00\x00\x00\x00\x00\x72') #Reset

    def deinit(self):
        self.uart.deinit()

    def SEN_Serial_ABCOn(self):
        self.uart.write(b'\xFF\x01\x79\xA0\x00\x00\x00\x00\xE6') #ABC On
        self.uart.wait_tx_done(1000)

    def SEN_Serial_ABCOff(self):
        self.uart.write(b'\xFF\x01\x79\x00\x00\x00\x00\x00\x86') #ABC Off
        self.uart.wait_tx_done(1000)

    def SEN_Serial_read(self):
        self.uart.write(b'\xFF\x01\x86\x00\x00\x00\x00\x00\x79') #get gas command
        self.uart.wait_tx_done(1000)
        Attempts=5
        while(Attempts>0):
            data=self._SerialRead()
            if(data!=False):
                return data
            Attempts-=1
            utime.sleep(1)
        return False

    def _SerialRead(self):
        print(str(self.uart.any()))
        if(self.uart.any()>=9):
            data=self.uart.read(9)
            return data
        else:
            return False

#References:
#https://techtutorialsx.com/2018/05/03/esp32-arduino-using-an-infrared-co2-sensor/
#https://wiki.dfrobot.com/Gravity__Analog_Infrared_CO2_Sensor_For_Arduino_SKU__SEN0219
#https://www.winsen-sensor.com/d/files/PDF/Infrared%20Gas%20Sensor/NDIR%20CO2%20SENSOR/MH-Z14%20CO2%20V2.4.pdf
#https://forum.arduino.cc/index.php?topic=589295.0
#Code by: João Reis & Rodrigo Soares
