import struct
from xerxes import MsgId, b2c, read_msg, send_msg


class XerxesLeaf:
    def __init__(self, address: int, serial_port) -> None:
        self.com = serial_port
        self.addr = address

    
    def read(self) -> bytes:
        send_msg(self.com, b"\x00", self.addr.to_bytes(1, "big"), MsgId.fetch)
        rpl = read_msg(self.com, timeout=15)
        return rpl.payload, rpl.message_id
    
    def __str__(self):
        return "XerxesLeaf(address={}, serial_port={})".format(self.addr, self.com)

class PressureLeaf(XerxesLeaf):
    def read(self) -> list:
        pl, msgid = super().read()
        p, ts, te1, te2 = struct.unpack("!ffff", pl)
        return [p, ts, te1, te2], msgid
    
    def __str__(self):
        return "PressureLeaf(address={}, serial_port={})".format(self.addr, self.com)


class StrainLeaf(XerxesLeaf):
    def read(self) -> list:
        pl, msgid = super().read()
        s, te1, te2 = struct.unpack("!fff", pl)
        return [s, 0, te1, te2], msgid
    
    def __str__(self):
        return "StrainLeaf(address={}, serial_port={})".format(self.addr, self.com)


class DistanceLeaf(XerxesLeaf):
    def read(self) -> list:
        pl, msgid = super().read()
        d, te1, te2 = struct.unpack("!fff", pl)
        return [d*1000.0, 0, te1, te2], msgid
    
    def __str__(self):
        return "DistanceLeaf(address={}, serial_port={})".format(self.addr, self.com)


class AngleLeaf(XerxesLeaf):
    def read(self) -> list:
        pl, msgid = super().read()
        x, y, te1, te2 = struct.unpack("!ffff", pl)
        return [x, y, te1, te2], msgid
    
    def __str__(self):
        return "AngleLeaf(address={}, serial_port={})".format(self.addr, self.com)

def leaf_generator(devId: int, address: int, serial_port: UART) -> XerxesLeaf:
    if isinstance(devId, bytes):
        devId = b2c(devId)
        
    assert isinstance(devId, int)

    if devId == 0x03 or devId == 0x04:
        return PressureLeaf(
            address=address,
            serial_port=serial_port
        )

    elif devId == 0x11:
        return StrainLeaf(
            address=address,
            serial_port=serial_port
            )

    elif devId == 0x40:
        return DistanceLeaf(
            address=address,
            serial_port=serial_port
            )

    elif devId == 0x30:
        return AngleLeaf(
            address=address,
            serial_port=serial_port
            )

    else:
        return XerxesLeaf(
            address=address,
            serial_port=serial_port
            )
