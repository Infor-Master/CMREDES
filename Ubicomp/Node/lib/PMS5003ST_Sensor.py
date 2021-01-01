from machine import UART
import utime

class PMS5003ST:

    # MAKE SURE TO CONNECT GROUND BETWEN DEVICES!
    # TX default use P3 on Lopy4
    # RX default use P4 on Lopy4
    # def CMD_changeMode = 0xe1
    # def CMD_Sleep = 0xe4
    # def CMD_Read = 0xe2
    # self.uart.write(b'\x42\x4D\xE1\x00\x00\x01\x70') #change to passive mode
    # self.uart.write(b'\x42\x4D\xE4\x00\x01\x01\x74') #wakeup
    # self.uart.write(b'\x42\x4D\xE4\x00\x00\x01\x73') #sleep
    # self.uart.write(b'\x42\x4D\xE2\x00\x00\x01\x71') #request read
    # Stable data should be got at least 30 seconds after the sensor wakeup from the sleep mode because of the fan's performance


    def __init__(self, TX, RX):
        self.uart = UART(1, 9600, bits=8, parity=None, stop=1, pins=(TX,RX))

    def deinit(self):
        self.uart.deinit()

    def PMSReadActive(self):
        Attempts=5
        while(Attempts>0):
            data=self._ReadActive()
            if(data!=False):
                return data
            Attempts-=1
            utime.sleep(1)
        return False

    def _ReadActive(self):
        if(self.uart.any()>40):
            data=bytearray(40)   #40 bits of data
            data=self.uart.read(40)
            datalist=self.PMSDecode(data)
            if(datalist[17]!=datalist[18]):
                return False
            return datalist
        else:
            return False


    def PMSDecode(self, data):
        datalist=list()
        datalist.append((data[4]<<8)|data[5])       #0      PM1.0 ug/m3
        datalist.append((data[6]<<8)|data[7])       #1      PM2.5 ug/m3
        datalist.append((data[8]<<8)|data[9])       #2      PM10 ug/m3
        datalist.append((data[10]<<8)|data[11])     #3      PM1.0 ug/m3 atmospheric
        datalist.append((data[12]<<8)|data[13])     #4      PM2.5 ug/m3 atmospheric
        datalist.append((data[14]<<8)|data[15])     #5      PM10 ug/m3 atmospheric
        datalist.append((data[16]<<8)|data[17])     #6      Count Particles > 0.3 um/0.1L
        datalist.append((data[18]<<8)|data[19])     #7      Count Particles > 0.5 um/0.1L
        datalist.append((data[20]<<8)|data[21])     #8      Count Particles > 1.0 um/0.1L
        datalist.append((data[22]<<8)|data[23])     #9      Count Particles > 2.5 um/0.1L
        datalist.append((data[24]<<8)|data[25])     #10     Count Particles > 5.0 um/0.1L
        datalist.append((data[26]<<8)|data[27])     #11     Count Particles > 10 um/0.1L
        datalist.append(((data[28]<<8)|data[29]))   #12 Formaldehyde mg/m^3
        datalist.append(((data[30]<<8)|data[31])/10)  #13     Temperature ºC
        datalist.append(((data[32]<<8)|data[33])/10)  #14     Humidity %
        datalist.append(data[36])                   #15     Firmware Version
        datalist.append(data[37])                   #16     Error Code
        datalist.append(data[38]<<8|data[39])       #17     Expected CheckSum
        check=0
        for i in range(38):
            check+=data[i]
        datalist.append(check)                      #18     Actual CheckSum
        return datalist

#References:
#https://github.com/fu-hsi/PMS/blob/master/src/PMS.cpp
#https://wiki.dfrobot.com/Air_Quality_Monitor__PM_2.5,_Formaldehyde,_Temperature_%26_Humidity_Sensor__SKU__SEN0233
