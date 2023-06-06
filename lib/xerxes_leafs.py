import struct
from xerxes import MsgId, b2c, read_msg, send_msg
import time


class XerxesLeaf:
    def __init__(self, address: int, serial_port, root_addr: int) -> None:
        self.com = serial_port
        self.addr = address
        self.root_addr = root_addr

    
    def read(self) -> bytes:
        send_msg(self.com, self.root_addr.to_bytes(1, "little"), b"\xFF", MsgId.sync)
        time.sleep(.2)
        send_msg(self.com, self.root_addr.to_bytes(1, "little"), self.addr.to_bytes(1, "little"), MsgId.fetch)
        rpl = read_msg(self.com, timeout=15)
        return rpl.payload, rpl.message_id
    
    def __str__(self):
        return f"XerxesLeaf(address={self.addr}, serial_port={self.com})"


class PressureLeaf(XerxesLeaf):
    def read(self) -> list:
        pl, msgid = super().read()
        p, ts, te1, te2 = struct.unpack("ffff", pl)
        return [p, ts, te1, te2], msgid
    
    def __str__(self):
        return f"PressureLeaf(address={self.addr}, serial_port={self.com})"


class StrainLeaf(XerxesLeaf):
    def read(self) -> list:
        pl, msgid = super().read()
        s, te1, te2 = struct.unpack("fff", pl)
        return [s, te1, te2], msgid
    
    def __str__(self):
        return f"StrainLeaf(address={self.addr}, serial_port={self.com})"


class DistanceLeaf(XerxesLeaf):
    def read(self) -> list:
        pl, msgid = super().read()
        d1, d2, raw1, raw2, te1, te2 = struct.unpack("ffffff", pl)
        return [d1*1000, d2*1000, raw1, raw2, te1, te2], msgid
    
    def __str__(self):
        return f"DistanceLeaf(address={self.addr}, serial_port={self.com})"


class AngleLeaf(XerxesLeaf):
    def read(self) -> list:
        pl, msgid = super().read()
        x, y, ts, te1, te2 = struct.unpack("fffff", pl)
        return [x, y, ts, te1, te2], msgid
    
    def __str__(self):
        return f"AngleLeaf(address={self.addr}, serial_port={self.com})"


def leaf_generator(devId: int, address: int, root_addr: int, serial_port: UART) -> XerxesLeaf:
    if isinstance(devId, bytes):
        devId = b2c(devId)

    assert isinstance(devId, int)

    if devId in [0x03, 0x04]:
        return PressureLeaf(
            address=address,
            serial_port=serial_port,
            root_addr=root_addr
        )

    elif devId == 0x11:
        return StrainLeaf(
            address=address,
            serial_port=serial_port,
            root_addr=root_addr
            )

    elif devId == 0x40:
        return DistanceLeaf(
            address=address,
            serial_port=serial_port,
            root_addr=root_addr
            )

    elif devId == 0x30:
        return AngleLeaf(
            address=address,
            serial_port=serial_port,
            root_addr=root_addr
            )

    else:
        return XerxesLeaf(
            address=address,
            serial_port=serial_port,
            root_addr=root_addr
            )
