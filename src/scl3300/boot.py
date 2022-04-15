# -*- coding: utf-8 -*-

import struct
from machine import Pin, SPI, freq
import scl3300
import utime as time

freq(240000000)


SCLK_Pin    = 15  # clock pin
MOSI_Pin    = 2   # mosi pin
MISO_Pin    = 4   # miso pin
CS_Pin      = 5   # chip select pin


class CS(Pin):
    def __init__(self, pin_nr) -> None:
        super().__init__(pin_nr, Pin.OUT, 1)


    def enable(self):
        self.value(0)
    

    def disable(self):
        self.value(1)


class Packet:
    def __init__(self, raw: bytes|bytearray) -> None:
        if isinstance(raw, bytes) or isinstance(raw, bytearray):
            self.VALUE = struct.unpack("!h", raw[1:3])[0]
            intrep = struct.unpack("!I", raw)[0]
        else:
            raise ValueError("Bytearray object expected, got", type(raw), " instead.")

        self.raw = intrep
        self.RW = (intrep & 2**31) >> 31
        self.ADDR = (intrep & (0b01111100 << 16)) >> 18
        self.RS = (intrep & (0b11 << 16)) >> 16
        self.DATA = (intrep & (0xFFFF << 8)) >> 8
        self.CRC = intrep & (0xFF)

        self.ERR = self.RS == 0b11

    
    def __repr__(self) -> str:
        return 'Packet(' + str(self.intrep) + ')'

    
class Angles:
    def __init__(self, x, y, z) -> None:
        self.x = x
        self.y = y
        self.z = z


    @staticmethod
    def from_raw(x, y, z) -> None:
        return Angles(
            (x * 180) / (2**15), 
            (y * 180) / (2**15), 
            (z * 180) / (2**15)
        )

    
    def __repr__(self) -> str:
        return "Angles(" + str(self.x) + "°, " + str(self.y) + "°, " + str(self.z) + "°)"


class SCL3300:
    def __init__(self, spinr:int, baudrate: int, sck: Pin, mosi: Pin, miso: Pin, cs: CS) -> None:
        self.cs = cs
        self.spi = SPI(spinr, baudrate, polarity=0, phase=0, bits=32, firstbit=SPI.MSB, sck=sck, mosi=mosi, miso=miso)


    def init(self) -> None:
        self._write(scl3300.Switch_to_bank_0)
        time.sleep_ms(1)

        self._write(scl3300.SW_Reset)
        time.sleep_ms(1) 

        self._write(scl3300.Change_to_mode_4)
        time.sleep_ms(1)

        self._write(scl3300.Enable_ANGLE)
        time.sleep_ms(100)

        self._write(scl3300.Read_Status_Summary)
        self._write(scl3300.Read_Status_Summary)
        self._write(scl3300.Read_Status_Summary)

        self._write(scl3300.Read_WHOAMI)
        self._write(scl3300.Read_WHOAMI)
    

    def _write(self, data: bytes|int) -> None:
        if isinstance(data, int):
            data = data.to_bytes(4, "big")
        try:
            self.cs.enable()
            self.spi.write(data)
        finally:
            self.cs.disable()


    def _exchange(self, data: bytes|int) -> Packet:
        if isinstance(data, int):
            data = data.to_bytes(4, "big")
        received = bytearray(len(data))
        try: 
            self.cs.enable()
            self.spi.write_readinto(data, received)
        finally:
            self.cs.disable()
        
        return Packet(received)
    

    def _read(self) -> bytes:
        received = bytearray(4)
        try:
            self.cs.enable()
            self.spi.readinto(received, 0x00)
        finally:
            self.cs.disable()

        return Packet(received)

    
    def read_ang(self) -> int:
        self._write(scl3300.Read_ANG_X)
        rdvalX = self._exchange(scl3300.Read_ANG_Y)
        rdvalY = self._exchange(scl3300.Read_ANG_Z)
        rdvalZ = self._read()
        
        return Angles.from_raw(rdvalX.VALUE, rdvalY.VALUE, rdvalZ.VALUE)
    

    def read_temp(self) -> int:
        self._write(scl3300.Read_Temperature)
        rdvalT = self._read()

        return rdvalT.VALUE / 18.9 - 273


cspin = CS(CS_Pin)
incl = SCL3300(
    2, 
    baudrate=4_000_000, 
    sck=Pin(SCLK_Pin), 
    mosi=Pin(MOSI_Pin),
    miso=Pin(MISO_Pin), 
    cs=cspin
    )

incl.init()

ns = 1000
while 1:
    ts = time.ticks_ms()
    x, y, z = 0, 0, 0
    for i in range(ns):
        xyz = incl.read_ang()
        x += xyz.x
        y += xyz.y
        z += xyz.z

    x /= ns
    y /= ns
    z /= ns


    print(Angles(x, y, z), "dt: ", time.ticks_ms() - ts,"ms")