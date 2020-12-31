from time import sleep
from machine import ADC
import AdvMath

class MQ131:
    #Sensor datasheet has a graphical representation of ppm of gas by Rs/R0. By obtaining this ratio and using the graphical funcion one can obtain the gas density in ppm
    #Rs is the resistance of the sensor that changes depending on the concentration of gas
    #R0 is the resistance of the sensor at a know concentration without the presence of gases (fresh air)
    #Rs/R0 of fresh air is 1 so R0=Rs/1
    #2 points of the gas function are selected (1.2 at 10ppm) and (8 at 1000ppm)
    #another point is used to find the intersect (6 at 500ppm)
    READ_SAMPLE_INTERVAL = const(500)
    READ_SAMPLE_TIMES = const(10)

    def __init__(self, pin, R0):
        self.pin = pin
        self.R0 = R0
        self.adc = ADC(bits=12)
        self.apin = self.adc.channel(pin=self.pin, attn=ADC.ATTN_11DB)

    def deinit(self):
        self.apin.deinit()
        self.adc.deinit()

    def MQRead(self):
        v=float(0)
        for i in range(READ_SAMPLE_TIMES):
            v += self.apin()
            sleep(READ_SAMPLE_INTERVAL/1000)
        return ((v/READ_SAMPLE_TIMES)*3.3/4096) #3.3v - ATTN_11DB & 4096 - 12bits

    def MQCalibrate_R0(self, volts):
        #Rs = (Vc * RL)/VRL - RL
        if (volts==0):
            return 0
        RS_air = ((5.0*10.0)/volts)-10.0
        R0_air = RS_air/1   #from graph, needs to be replaced with real data
        return R0_air

    def MQGet_PPB(self, volts):
        if (volts==0):
            return 0
        Rs = ((5.0*10.0)/volts)-10.0
        m=AdvMath.log10(1.2/10)/AdvMath.log10(8/1000)
        b=AdvMath.log10(6)-(m*AdvMath.log10(500))
        if (Rs==0):
            return 0
        return pow(10,(((AdvMath.log10(Rs/self.R0))-b)/m))


#References:
#https://www.winsen-sensor.com/d/files/PDF/Semiconductor%20Gas%20Sensor/mq131(high-concentration)-ver1_4-manual.pdf
#https://jayconsystems.com/blog/understanding-a-gas-sensor
#https://www.instructables.com/id/How-to-Detect-Concentration-of-Gas-by-Using-MQ2-Se/
#Code by: Rodrigo Soares
