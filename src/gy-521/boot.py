# -*- coding: utf-8 -*-

from math import atan2, sqrt, pi
from machine import Pin, I2C, freq, SoftI2C
import struct
from config import *
import utime as time

freq(240000000)

i2c = I2C(1, scl=Pin(SCL_Pin), sda=Pin(SDA_Pin), freq=400000)


def avgXYZ(buf):
    x, y, z = 0, 0, 0
    samples = int(len(buf)/6)
    for i in range(samples):
        x += buf[0]*256 + buf[1]
        y += buf[2]*256 + buf[3]
        z += buf[4]*256 + buf[5]
    
    return [
        float(x) / samples, 
        float(y) / samples, 
        float(z) / samples
        ]


class MPU6050:
    def __init__(self, addr: int, i2c: I2C) -> None:
        self.iic = i2c
        self.addr = addr
        self.write_reg(
            regnr=107, # reset and config the device
            value=0
            )

        # reset the accelerometer scale to +/-2g
        self.write_reg(28, 0)

        #reset FIFO:
        self.write_reg(regnr=106, value=0b00000100)

        # enable FIFO operation:
        self.write_reg(regnr=106, value=0b01000000)


    def set_lpf(self, magnitude: int) -> None:
        assert magnitude >= 0 and magnitude <= 6
        self.write_reg(
            26,
            magnitude
        )


    def fifo_enable(self):
        # push only accelerometer data to fifo
        self.write_reg(regnr=35, value=0b00001000)
        self.fifo_enabled = True


    def fifo_disable(self):
        # disable acc data to fifo transfer
        self.write_reg(regnr=35, value=0b00000000)
        self.fifo_enabled = False


    @property
    def fifo_count(self) -> int:
        return struct.unpack("!h", self.read_mem(114, 2))[0]


    def fifo_pop(self) -> int:
        return self.read_reg(116)

    
    def fifo_pop_xyz(self) -> int:
        was_en = self.fifo_enabled
        if was_en:
            self.fifo_disable()

        if self.fifo_count:
            buf = []
            for i in range(6):
                buf.append(self.fifo_pop())
            if was_en: self.fifo_enable()
            return [x, y, z]
        
        if was_en:
            self.fifo_enable()
        return []

    
    def fifo_read(self) -> list:
        was_en = self.fifo_enabled
        if was_en:
            self.fifo_disable()

        buf = []
        
        for i in range(self.fifo_count):
            buf.append(self.read_reg(116))
        
        if was_en:
            self.fifo_enable()

        return buf


    def write_reg(self, regnr: int, value: int) -> bool:
        ack = self.iic.writeto(
            self.addr, 
            bytearray([regnr, value])
        )
        return ack == 2


    def read_reg(self, regnr:int) -> int:
        ack = self.iic.writeto(
            self.addr, 
            bytearray([regnr])
        )

        val = self.iic.readfrom(
            self.addr,  # read from
            1  # 1 byte
        )
        return struct.unpack("!b", val)[0]


    def read_mem(self, regnr: int, nbytes: int):
        return self.iic.readfrom_mem(
            self.addr,
            regnr,
            nbytes
        )

def inclXY(xyz):
    accelX = xyz[0]
    accelY = xyz[1]
    accelZ = xyz[2]
    accelAngleX = atan2(accelY, accelZ) * 180/pi
    accelAngleY = atan2(-accelX, sqrt(accelY*accelY + accelZ*accelZ)) * 180/pi
    return accelAngleX, accelAngleY


mpu = MPU6050(i2c.scan()[0], i2c)
mpu.set_lpf(6)

def mainloop():
    mpu.fifo_enable()
    time.sleep(.1)
    mpu.fifo_disable()

    buf = mpu.fifo_read()
    print(avgXYZ(buf))

