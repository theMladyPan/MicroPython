import struct
import time
from micropython import const


PROTOCOL_VERSION_MAJOR = const(1)
PROTOCOL_VERSION_MIN = const(2)


def b2c(data: bytes) -> int:
    return struct.unpack("!B", data)[0]


def c2b(data: int) -> bytes:
    return data.to_bytes(1, "big")


class MsgId:
    ping_req        = struct.pack("H", 0x0000)
    ping_reply      = struct.pack("H", 0x0001)
    ack_ok          = struct.pack("H", 0x0002)
    ack_nok         = struct.pack("H", 0x0003)
    fetch           = struct.pack("H", 0x0100)
    sync            = struct.pack("H", 0x0101)
    set             = struct.pack("H", 0x0200)
    read            = struct.pack("H", 0x0201)
    read_value      = struct.pack("H", 0x0202)
    fetch_generic   = struct.pack("H", 0x1000)
    


class XerxesMessage:
    def __init__(self, source: bytes, destination: bytes, length: int, message_id: int, payload: bytes) -> None:
        self.source = source
        self.destination = destination
        self.length = length
        self.message_id = message_id
        self.payload = payload
    
    @property
    def message_id_bytes(self) -> bytes:
        return self.message_id.to_bytes(2, "little")


def checksum(message: bytes) -> bytes:
    summary = sum(message)
    summary ^= 0xFF  # get complement of summary
    summary += 1  # get 2's complement
    summary %= 0x100  # get last 8 bits of summary
    return summary.to_bytes(1, "little")


def send_msg(com: UART, sender: bytes, destination: bytes, payload: bytes, *, tx_en: bool=None):    
    msg = b"\x01"
    msg += (len(payload) + 5).to_bytes(1, "little")  # LEN
    msg += sender
    msg += destination #  DST
    msg += payload
    msg += checksum(msg)

    if tx_en:
        # activate transmission mode
        tx_en.on()

    com.write(msg)

    if tx_en:
        # deactivate transmission mode
        tx_en.off()

    
class StopWatch:
    def __init__(self, timeout_ms: int):
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
    return hex(struct.unpack("B", byte)[0])


def read_msg(com: UART, *, timeout: int=0) -> XerxesMessage:
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
    msg_len = struct.unpack("B", com.read(1))[0]
    
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

    msg_id = struct.unpack("H", msg_id_raw)[0]

    # read and unpack all data into array
    raw_msg = bytes(0)
    for i in range(int(msg_len -    7)):
        next_byte = com.read(1)
        if next_byte == None or sw.elapsed():
            raise RuntimeError("Uart timeout")
        raw_msg += next_byte
        checksum += struct.unpack("B", next_byte)[0]
    
    #read checksum
    rcvd_chks = com.read(1)
    checksum += struct.unpack("B", rcvd_chks)[0]
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