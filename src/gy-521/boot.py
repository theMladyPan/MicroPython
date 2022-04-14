# -*- coding: utf-8 -*-

from machine import Pin, I2C, freq, SoftI2C
import struct
from config import *
import utime as time

freq(240000000)

i2c = I2C(1, scl=Pin(SCL_Pin), sda=Pin(SDA_Pin), freq=400000)


class MPU6050:
    def __init__(self, addr: int, i2c: I2C) -> None:
        self.iic = i2c
        self.addr = addr
        self.write_reg(
            regnr=107, # reset and config the device
            value=0
            )

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
        return struct.unpack(
            "!"+"b"*nbytes,
            self.iic.readfrom_mem(
                self.addr,
                regnr,
                nbytes
            )
        )

class Acc():
    def __init__(self, i2c, addr=0x68):
        self.iic = i2c
        self.addr = addr
        self.iic.writeto(self.addr, bytearray([107, 0]))

    def get_raw_values(self):
        a = self.iic.readfrom_mem(self.addr, 0x3B, 14)
        return a

    def acc_xyz(self):
        return self.iic.readfrom_mem(self.addr, 0x3B, 6)

    def get_ints(self):
        b = self.get_raw_values()
        c = []
        for i in b:
            c.append(i)
        return c

    def bytes_toint(self, firstbyte, secondbyte):
        if not firstbyte & 0x80:
            return firstbyte << 8 | secondbyte
        return - (((firstbyte ^ 255) << 8) | (secondbyte ^ 255) + 1)

    def get_values(self):
        raw_ints = self.get_raw_values()
        vals = {}
        vals["AcX"] = self.bytes_toint(raw_ints[0], raw_ints[1])
        vals["AcY"] = self.bytes_toint(raw_ints[2], raw_ints[3])
        vals["AcZ"] = self.bytes_toint(raw_ints[4], raw_ints[5])
        vals["Tmp"] = self.bytes_toint(raw_ints[6], raw_ints[7]) / 340.00 + 36.53
        vals["GyX"] = self.bytes_toint(raw_ints[8], raw_ints[9])
        vals["GyY"] = self.bytes_toint(raw_ints[10], raw_ints[11])
        vals["GyZ"] = self.bytes_toint(raw_ints[12], raw_ints[13])
        return vals  # returned in range of Int16
        # -32768 to 32767

    def val_test(self):  # ONLY FOR TESTING! Also, fast reading sometimes crashes IIC
        from time import sleep
        while 1:
            print(self.get_values())
            sleep(0.05)

gy = Acc(i2c)
mpu = MPU6050(i2c.scan()[0], i2c)