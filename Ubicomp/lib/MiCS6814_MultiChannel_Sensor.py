from machine import I2C
import math
import utime

class MiCS6814:
    DEFAULT_I2C_ADDR = const(0x04)

    ADDR_IS_SET = const(0)           # if this is the first time to run, if 1126, set
    ADDR_FACTORY_ADC_NH3 = const(2)
    ADDR_FACTORY_ADC_CO = const(4)
    ADDR_FACTORY_ADC_NO2 = const(6)

    ADDR_USER_ADC_HN3 = const(8)
    ADDR_USER_ADC_CO = const(10)
    ADDR_USER_ADC_NO2 = const(12)
    ADDR_IF_CALI = const(14)          # IF USER HAD CALI

    ADDR_I2C_ADDRESS = const(20)

    CH_VALUE_NH3 = const(1)
    CH_VALUE_CO = const(2)
    CH_VALUE_NO2 = const(3)

    CMD_ADC_RES0 = const(1)           # NH3
    CMD_ADC_RES1 = const(2)           # CO
    CMD_ADC_RES2 = const(3)           # NO2
    CMD_ADC_RESALL = const(4)           # ALL CHANNEL
    CMD_CHANGE_I2C = const(5)           # CHANGE I2C
    CMD_READ_EEPROM = const(6)           # READ EEPROM VALUE, RETURN UNSIGNED INT
    CMD_SET_R0_ADC = const(7)           # SET R0 ADC VALUE
    CMD_GET_R0_ADC = const(8)           # GET R0 ADC VALUE
    CMD_GET_R0_ADC_FACTORY = const(9)           # GET FACTORY R0 ADC VALUE
    CMD_CONTROL_LED = const(10)
    CMD_CONTROL_PWR = const(11)

    def __init__(self, SDA, SCL):
        self.i2c = I2C(0, pins=(SDA, SCL), baudrate=100000)
        self.begin(DEFAULT_I2C_ADDR)
        self.res0 = [3]

    def deinit(self):
        self.i2c.deinit()
#/*********************************************************************************************************
#** Function name:           begin
#** Descriptions:            initialize I2C
#*********************************************************************************************************/
    def begin(self, addr):
        self.__version = 1
        self.r0_inited = False
        self.i2caddr = addr
        self.__version = self.getVersion()

    def getVersion(self):
        if(self.get_addr_dta_2(CMD_READ_EEPROM, ADDR_IS_SET) == 1126):
            self.__version = 2
            return 2
        else:
            self.__version = 1
            return 1
#/*********************************************************************************************************
#** Function name:           sendI2C
#** Descriptions:            send one byte to I2C Wire
#*********************************************************************************************************/
    def sendI2C(self, dta):
        self.i2c.writeto(self.i2caddr, bytes([dta]))

    def get_addr_dta_1(self, addr_reg):
        self.sendI2C(addr_reg)
        utime.sleep(2)
        raw=self.i2c.readfrom(self.i2caddr, 2)
        dta=raw[0]
        dta <<= 8
        dta += raw[1]
        if(addr_reg == CH_VALUE_NH3):
            if(dta>0):
                self.adcValueR0_NH3_Buf = dta
            else:
                dta = self.adcValueR0_NH3_Buf
        elif(addr_reg == CH_VALUE_CO):
            if(dta>0):
                self.adcValueR0_CO_Buf = dta
            else:
                dta = self.adcValueR0_CO_Buf
        elif(addr_reg == CH_VALUE_NO2):
            if(dta>0):
                self.adcValueR0_NO2_Buf = dta
            else:
                dta = self.adcValueR0_NO2_Buf
        else:
            pass
        return dta

    def get_addr_dta_2(self, addr_reg, __dta):
        self.i2c.writeto(self.i2caddr, bytes([addr_reg, __dta]))
        utime.sleep(2)
        raw=self.i2c.readfrom(self.i2caddr, 2)
        dta=raw[0]
        dta <<= 8
        dta += raw[1]
        return dta

#/*********************************************************************************************************
#** Function name:           readData
#** Descriptions:            read 4 bytes from I2C slave
#*********************************************************************************************************/
    def readData(self, cmd):
        self.sendI2C(cmd)
        utime.sleep(2)
        buffer[4]=self.i2c.readfrom(self.i2caddr, 4)
        checksum=(buffer[0]+buffer[1]+buffer[2])
        if(checksum!=buffer[3]):
            return -4   #checksum wrong
        Data = ((buffer[1] << 8) + buffer[2])
        return Data
#/*********************************************************************************************************
#** Function name:           readR0
#** Descriptions:            read R0 stored in slave MCU
#*********************************************************************************************************/
    def readR0(self):
        rtnData = 0
        addr = [0x11, 0x12, 0x13]
        for i in range(3):
            rtnData = self.readData(addr[i])
            if rtnData>0:
                self.res0[i] = rtnData
            else:
                return rtnData
        return 1
#/*********************************************************************************************************
#** Function name:           readR
#** Descriptions:            read resistance value of each channel from slave MCU
#*********************************************************************************************************/
    def readR(self):
        rtnData = 0
        addr = [0x01, 0x02, 0x03]
        for i in range(3):
            rtnData = self.readData(addr[i])
            if rtnData>0:
                self.res[i] = rtnData
            else:
                return rtnData
        return 1

#/*********************************************************************************************************
#** Function name:           calcGas
#** Descriptions:            calculate gas concentration of each channel from slave MCU
#** Parameters:
#                            gas - gas type
#** Returns:
#                            float value - concentration of the gas
#*********************************************************************************************************/
    def calcGas(self, gas):
        if(1 == self.__version):
            if(self.r0_inited==False):
                if(self.readR0()>=0):
                    r0_inited = true
                else:
                    return -1
            if(self.readR()<0):
                return -2
            ratio0=self.res[0]/self.res0[0]
            ratio1=self.res[1]/self.res0[1]
            ratio2=self.res[2]/self.res0[2]
        elif(2 == self.__version):
            #ledOn()
            A0_0 = self.get_addr_dta_2(6, ADDR_USER_ADC_HN3)
            A0_1 = self.get_addr_dta_2(6, ADDR_USER_ADC_CO)
            A0_2 = self.get_addr_dta_2(6, ADDR_USER_ADC_NO2)

            An_0 = self.get_addr_dta_1(CH_VALUE_NH3)
            An_1 = self.get_addr_dta_1(CH_VALUE_CO)
            An_2 = self.get_addr_dta_1(CH_VALUE_NO2)

            ratio0 = An_0/A0_0*(1023.0-A0_0)/(1023.0-An_0)
            ratio1 = An_1/A0_1*(1023.0-A0_1)/(1023.0-An_1)
            ratio2 = An_2/A0_2*(1023.0-A0_2)/(1023.0-An_2)

        #next code was added/modded by jack
        c = 0
        if (gas=='CO'):
            c = math.pow(ratio1,-1.179)*4.385
        elif(gas=='NO2'):
            c = math.pow(ratio2,1.007)/6.855
        elif(gas=='NH3'):
            c = math.pow(ratio0,-1.67)/1.47
        elif(gas=='C3H8'):
            c = math.pow(ratio0,-2.518)*570.164
        elif(gas=='C4H10'):
            c = math.pow(ratio0, -2.138)*398.107
        elif(gas=='CH4'):
            c = math.pow(ratio1, -4.363)*630.957
        elif(gas=='H2'):
            c = math.pow(ratio1, -1.8)*0.73
        elif(gas=='C2H5OH'):
            c = math.pow(ratio1, -1.552)*1.622
        else:
            c = 0
        #if (2==self.__version):
            #ledOff()
        if(math.isnan(c)==True):
            return -3
        else:
            return c

#/*********************************************************************************************************
#** Function name:           calcAllGases
#** Descriptions:            calculate gas concentration of each channel from slave MCU
#** Returns:
#                            list float value - concentration of the gases
#*********************************************************************************************************/

    def calcAllGases(self):
        if(1 == self.__version):
            if(self.r0_inited==False):
                if(self.readR0()>=0):
                    r0_inited = true
                else:
                    return -1
            if(self.readR()<0):
                return -2
            ratio0=self.res[0]/self.res0[0]
            ratio1=self.res[1]/self.res0[1]
            ratio2=self.res[2]/self.res0[2]
        elif(2 == self.__version):
            #ledOn()
            A0_0 = self.get_addr_dta_2(6, ADDR_USER_ADC_HN3)
            A0_1 = self.get_addr_dta_2(6, ADDR_USER_ADC_CO)
            A0_2 = self.get_addr_dta_2(6, ADDR_USER_ADC_NO2)

            An_0 = self.get_addr_dta_1(CH_VALUE_NH3)
            An_1 = self.get_addr_dta_1(CH_VALUE_CO)
            An_2 = self.get_addr_dta_1(CH_VALUE_NO2)

            ratio0 = An_0/A0_0*(1023.0-A0_0)/(1023.0-An_0)
            ratio1 = An_1/A0_1*(1023.0-A0_1)/(1023.0-An_1)
            ratio2 = An_2/A0_2*(1023.0-A0_2)/(1023.0-An_2)

        #next code was added/modded by jack
        c = list()
        c.append(math.pow(ratio1,-1.179)*4.385) #CO
        c.append(math.pow(ratio2,1.007)/6.855)  #NO2
        c.append(math.pow(ratio0,-1.67)/1.47)    #NH3
        c.append(math.pow(ratio0,-2.518)*570.164)    #C3H8
        c.append(math.pow(ratio0, -2.138)*398.107)   #C4H10
        c.append(math.pow(ratio1, -4.363)*630.957)   #CH4
        c.append(math.pow(ratio1, -1.8)*0.73)    #H2
        c.append(math.pow(ratio1, -1.552)*1.622) #C2H5OH
        #if (2==self.__version):
            #ledOff()
        return c
