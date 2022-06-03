import struct
import time


def b2c(data: bytes) -> int:
    return struct.unpack("!B", data)[0]


def c2b(data: int) -> bytes:
    return data.to_bytes(1, "big")


class MsgId:
    ping_req = struct.pack("!H", 0x0000)
    ping_reply = struct.pack("!H", 0x0001)
    ack_ok = struct.pack("!H", 0x0002)
    ack_nok = struct.pack("!H", 0x0003)
    fetch = struct.pack("!H", 0x0100)
    sync = struct.pack("!H", 0x0101)


class XerxesMessage:
    def __init__(self, source: bytes, destination: bytes, length: int, message_id: int, payload: bytes) -> None:
        self.source = source
        self.destination = destination
        self.length = length
        self.message_id = message_id
        self.payload = payload


class XerxesLeaf:
    def __init__(self, address: int, serial_port) -> None:
        self.com = serial_port
        self.addr = address

    
    def read(self) -> bytes:
        send_msg(self.com, b"\x00", self.addr.to_bytes(1, "big"), MsgId.fetch)
        rpl = read_msg(self.com, timeout=15)
        return rpl.payload, rpl.message_id
    

class PressureLeaf(XerxesLeaf):
    def read(self) -> list:
        pl, msgid = super().read()
        p, ts, te1, te2 = struct.unpack("!ffff", pl)
        return [p, ts, te1, te2], msgid


class StrainLeaf(XerxesLeaf):
    def read(self) -> list:
        pl, msgid = super().read()
        s, te1, te2 = struct.unpack("!III", pl)
        return [s, te1, te2], msgid


class DistanceLeaf(XerxesLeaf):
    def read(self) -> list:
        pl, msgid = super().read()
        d, te1, te2 = struct.unpack("!III", pl)
        return [d, te1, te2], msgid


class AngleLeaf(XerxesLeaf):
    def read(self) -> list:
        pl, msgid = super().read()
        x, y, te1, te2 = struct.unpack("!ffff", pl)
        return [x, y, te1, te2], msgid


def leaf_generator(devId: int, address: int, serial_port: UART) -> XerxesLeaf:
    if isinstance(devId, bytes):
        devId = b2c(devId)

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


def checksum(message: bytes) -> bytes:
    summary = sum(message)
    summary ^= 0xFF  # get complement of summary
    summary += 1  # get 2's complement
    summary %= 0x100  # get last 8 bits of summary
    return summary.to_bytes(1, "big")


def send_msg(com, sender, destination, payload: bytes, *, tx_en=None):    
    msg = b"\x01"
    msg += (len(payload) + 5).to_bytes(1, "big")  # LEN
    msg += sender
    msg += destination #  DST
    msg += payload  # MSGID
    msg += checksum(msg)

    if tx_en:
        # activate transmission mode
        tx_en.on()

    com.write(msg)

    if tx_en:
        # deactivate transmission mode
        tx_en.off()

    
class StopWatch:
    def __init__(self, timeout_ms):
        self.start = time.ticks_ms()
        self.timeout = timeout_ms
        
    def elapsed(self):
        if self.timeout:
            return ( time.ticks_ms() - self.start ) > self.timeout
        else:
            return False
    
    def running(self):
        if self.timeout:
            return ( time.ticks_ms() - self.start ) < self.timeout
        else:
            return True


def to_hex(byte):
    return hex(struct.unpack("!B", byte)[0])


def read_msg(com, *, timeout=0):
    # wait for start of message
    sw = StopWatch(timeout)
        
    next_byte = com.read(1)
    while next_byte != b"\x01":
        next_byte = com.read(1)
        if sw.elapsed():
            raise RuntimeError("Uart timeout")

    checksum = 0x01
    # read message length
    # msg_len = int(com.read(1).hex(), 16)
    msg_len = struct.unpack("!B", com.read(1))[0]
    
    checksum += msg_len

    if sw.elapsed():
        raise RuntimeError("Uart timeout")
    #read source and destination address
    src = com.read(1)
    if sw.elapsed() or src == None:
        raise RuntimeError("Uart timeout")
    dst = com.read(1)
    if sw.elapsed() or dst == None:
        raise RuntimeError("Uart timeout")

    for i in [src, dst]:
        checksum += struct.unpack("!B", i)[0]

    # read message ID
    msg_id_raw = com.read(2)
    if sw.elapsed(): 
        raise RuntimeError("Uart timeout")
    
    if(len(msg_id_raw)!=2):
        raise RuntimeError("Invalid message received")
    for i in msg_id_raw:
        checksum += i

    msg_id = struct.unpack("!H", msg_id_raw)[0]

    # read and unpack all data into array
    raw_msg = bytes(0)
    for i in range(int(msg_len -    7)):
        next_byte = com.read(1)
        if next_byte == None or sw.elapsed():
            raise RuntimeError("Uart timeout")
        raw_msg += next_byte
        checksum += struct.unpack("!B", next_byte)[0]
    
    #read checksum
    rcvd_chks = com.read(1)
    checksum += struct.unpack("!B", rcvd_chks)[0]
    checksum %= 0x100
    if checksum:
        print("received checksum: ", checksum)
        raise RuntimeError("Invalid checksum received")
    
    return XerxesMessage(
        source=src,
        destination=dst,
        length=msg_len,
        message_id=msg_id,
        payload=raw_msg
    )


def to_celsius(millikelvin):
    return (millikelvin / 1000) - 273.15


def to_mmH2O(millipascal):
    return ( millipascal / 9806.65 )