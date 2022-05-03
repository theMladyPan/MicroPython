import struct
import time
from machine import Pin, SPI


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
        return "Angles(" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ")"


class Vector:
    def __init__(self, x, y, z) -> None:
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self) -> str:
        return "Vector(" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ")"


class SCL3300:
    class Cmd:
        Read_ACC_X = 0x040000F7
        Read_ACC_Y = 0x080000FD
        Read_ACC_Z = 0x0C0000FB
        Read_STO = 0x100000E9
        Enable_ANGLE = 0xB0001F6F
        Read_ANG_X = 0x240000C7
        Read_ANG_Y = 0x280000CD
        Read_ANG_Z = 0x2C0000CB
        Read_Temperature = 0x140000EF
        Read_Status_Summary = 0x180000E5
        Read_ERR_FLAG1 = 0x_1C0000E
        Read_ERR_FLAG2 = 0x200000C1
        Read_CMD = 0x340000DF
        Change_to_mode_1 = 0xB400001F
        Change_to_mode_2 = 0xB4000102
        Change_to_mode_3 = 0xB4000225
        Change_to_mode_4 = 0xB4000338
        Set_power_down_mode = 0xB400046B
        Wake_up_from_power_down_mode = 0xB400001F
        SW_Reset = 0xB4002098
        Read_WHOAMI = 0x40000091
        Read_SERIAL1 = 0x640000A7
        Read_SERIAL2 = 0x680000AD
        Read_current_bank = 0x7C0000B3
        Switch_to_bank_0 = 0xFC000073
        Switch_to_bank_1 = 0xFC00016E

        ANG_X_B = b'$\x00\x00\xc7'
        ANG_Y_B = b'(\x00\x00\xcd'
        ANG_Z_B = b',\x00\x00\xcb'
        ACC_X_B = b'\x04\x00\x00\xf7'


    def __init__(self, spinr:int, baudrate: int, sck: Pin, mosi: Pin, miso: Pin, cs: CS) -> None:
        self.cs = cs
        self.spi = SPI(spinr, baudrate, polarity=0, phase=0, bits=32, firstbit=SPI.MSB, sck=sck, mosi=mosi, miso=miso)


    def init(self) -> None:
        self._write(self.Cmd.Switch_to_bank_0)
        time.sleep_ms(1)

        self._write(self.Cmd.SW_Reset)
        time.sleep_ms(1) 

        self._write(self.Cmd.Change_to_mode_4)
        time.sleep_ms(1)

        self._write(self.Cmd.Enable_ANGLE)
        time.sleep_ms(100)

        self._write(self.Cmd.Read_Status_Summary)
        self._write(self.Cmd.Read_Status_Summary)
        self._write(self.Cmd.Read_Status_Summary)

        self._write(self.Cmd.Read_WHOAMI)
        self._write(self.Cmd.Read_WHOAMI)
    

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

    
    def read_ang(self) -> Angles:
        self._write(self.Cmd.Read_ANG_X)
        rdvalX = self._exchange(self.Cmd.Read_ANG_Y)
        rdvalY = self._exchange(self.Cmd.Read_ANG_Z)
        rdvalZ = self._read()
        
        return Angles.from_raw(rdvalX.VALUE, rdvalY.VALUE, rdvalZ.VALUE)

    
    def read_acc(self) -> Vector:
        self._write(self.Cmd.Read_ACC_X)
        rdvalX = self._exchange(self.Cmd.Read_ACC_Y)
        rdvalY = self._exchange(self.Cmd.Read_ACC_Z)
        rdvalZ = self._read()
        
        return Vector(rdvalX.VALUE, rdvalY.VALUE, rdvalZ.VALUE)
    

    def read_temp(self) -> int:
        self._write(self.Cmd.Read_Temperature)
        rdvalT = self._read()

        return rdvalT.VALUE / 18.9 - 273

    