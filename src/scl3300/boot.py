# -*- coding: utf-8 -*-

from machine import Pin, SPI, freq
from scl3300 import Enable_ANGLE, Read_ANG_X, Read_WHOAMI, SW_Reset, Change_to_mode_4, Read_Status_Summary
import utime as time

freq(240000000)

SCLK_Pin    = 15  #clock pin
MOSI_Pin    = 2  #mosi pin
MISO_Pin    = 4   #miso pin
CS_Pin      = 5    #chip select pin

class CS(Pin):
    def __init__(self, pin_nr) -> None:
        super().__init__(pin_nr, Pin.OUT, 1)

    def enable(self):
        self.value(0)
    
    def disable(self):
        self.value(1)


class SCL3300:
    def __init__(self, spinr:int, baudrate: int, sck: Pin, mosi: Pin, miso: Pin, cs: CS) -> None:
        self.cs = cs
        self.spi = SPI(spinr, baudrate, polarity=0, phase=0, bits=32, firstbit=SPI.MSB, sck=sck, mosi=mosi, miso=miso)
    
    def write(self, data: bytes|int) -> None:
        if isinstance(data, int):
            data = data.to_bytes(4, "big")
        try:
            self.cs.enable()
            self.spi.write(data)
        finally:
            self.cs.disable()

    def exchange(self, data: bytes|int) -> bytes:
        if isinstance(data, int):
            data = data.to_bytes(4, "big")
        received = bytearray(len(data))
        try: 
            self.cs.enable()
            received = self.spi.write_readinto(data, received)
        finally:
            self.cs.disable()
            return received
    
    def read(self, n) -> bytes:
        received = bytearray(n)
        try:
            self.cs.enable()
            received = self.spi.readinto(received, 0x00)
        finally:
            return received


cspin = CS(CS_Pin)
incl = SCL3300(
    2, 
    baudrate=1_000_000, 
    sck=Pin(SCLK_Pin), 
    mosi=Pin(MOSI_Pin),
    miso=Pin(MISO_Pin), 
    cs=cspin
    )


incl.write(SW_Reset)
time.sleep_ms(1)

incl.write(Change_to_mode_4)
time.sleep_ms(1)

incl.write(Enable_ANGLE)
time.sleep_ms(100)

for i in range(3):
    print("Status: ", incl.exchange(Read_Status_Summary))

while 1:
    print("X: ", incl.exchange(Read_ANG_X))
    time.sleep(1)