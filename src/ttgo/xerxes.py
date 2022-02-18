import struct
import time

def checksum(message: bytes) -> bytes:
    summary = sum(message)
    summary ^= 0xFF  # get complement of summary
    summary += 1  # get 2's complement
    summary %= 0x100  # get last 8 bits of summary
    return summary.to_bytes(1, "big")


def send_msg(com, sender, destination, payload: bytes, *, tx_en=None):    
    SOH = b"\x01"
    SOT = b"\x02"

    msg = SOH  # SOH
    msg += (len(payload) + 6).to_bytes(1, "big")  # LEN
    msg += sender
    msg += destination #  DST
    msg += SOT
    msg += payload  # MSGID
    msg += checksum(msg)

    if tx_en:
        # activate transmission mode
        tx_en.on()

    com.write(msg)

    if tx_en:
        # deactivate transmission mode
        tx_en.off()
    #time.sleep(0.001)
    #com.write(os.urandom(128))
    
class StopWatch:
    def __init__(self, timeout=0):
        self.start = time.time()
        self.timeout = timeout
        
    def elapsed(self):
        if self.timeout:
            return ( time.time() - self.start ) > self.timeout
        else:
            return False
    
    def running(self):
        if self.timeout:
            return ( time.time() - self.start ) < self.timeout
        else:
            return True
        
def to_hex(byte):
    return hex(struct.unpack("!B", byte)[0])

def read_raw(com, *, timeout=0):
    # wait for start of message
    sw = StopWatch(timeout)
        
    next_byte = com.read(1)
    while next_byte != b"\x01":
        next_byte = com.read(1)
        if sw.elapsed():
            return None

    checksum = 0x01
    # read message length
    # msg_len = int(com.read(1).hex(), 16)
    msg_len = struct.unpack("!B", com.read(1))[0]
    print(msg_len)
    
    checksum += msg_len

    if sw.elapsed(): return None
    #read source and destination address
    src = com.read(1)
    if sw.elapsed() or src == None: return None
    dst = com.read(1)
    if sw.elapsed() or dst == None: return None

    sot = com.read(1)
    if sw.elapsed(): return None

    for i in [src, dst, sot]:
        checksum += struct.unpack("!B", i)[0]
    
    # read and unpack all data into array, assiming it is uint32_t, big-endian
    msg_array = []
    for i in range(int(msg_len-6)):
        next_byte = com.read(1)
        uchar = struct.unpack("!B", next_byte)[0]
        checksum += uchar
        msg_array.append(next_byte)
    
    #read checksum
    rcvd_chks = com.read(1)
    checksum += struct.unpack("!B", rcvd_chks)[0]
    checksum %= 0x100
    if checksum:
        print("received checksum: ", checksum)
        raise IOError("Invalid checksum received")

    return {
        "source": to_hex(src),
        "destination": to_hex(dst),
        "length": msg_len,
        "payload": msg_array 
        }

def read_msg(com, *, timeout=0):
    # wait for start of message
    sw = StopWatch(timeout)
        
    next_byte = com.read(1)
    while next_byte != b"\x01":
        next_byte = com.read(1)
        if sw.elapsed():
            return None

    checksum = 0x01
    # read message length
    # msg_len = int(com.read(1).hex(), 16)
    msg_len = struct.unpack("!B", com.read(1))[0]
    print(msg_len)
    
    checksum += msg_len

    if sw.elapsed(): return None
    #read source and destination address
    src = com.read(1)
    if sw.elapsed() or src == None: return None
    dst = com.read(1)
    if sw.elapsed() or dst == None: return None

    sot = com.read(1)
    if sw.elapsed(): return None

    for i in [src, dst, sot]:
        checksum += struct.unpack("!B", i)[0]

    # read message ID
    msg_id_raw = com.read(4)
    if sw.elapsed(): return None
    
    if(len(msg_id_raw)!=4):
        raise RuntimeError("Invalid message received")
    for i in msg_id_raw:
        checksum += i

    msg_id = struct.unpack("!I", msg_id_raw)[0]

    # read and unpack all data into array, assiming it is uint32_t, big-endian
    msg_array = []
    for i in range(int((msg_len-10)/4)):
        next_word = com.read(4)
        for i in next_word:
            checksum += i
        msg_array.append(struct.unpack("!I", next_word)[0])
    
    #read checksum
    rcvd_chks = com.read(1)
    checksum += struct.unpack("!B", rcvd_chks)[0]
    checksum %= 0x100
    if checksum:
        print("received checksum: ", checksum)
        raise IOError("Invalid checksum received")

    return {
        "source": to_hex(src),
        "destination": to_hex(dst),
        "length": msg_len,
        "message_id": msg_id,
        "payload": msg_array 
        }

def to_celsius(millikelvin):
    return (millikelvin / 1000) - 273.15

def to_mmH2O(microbar):
    return ( microbar / 1000000 ) * 10197.162129779;

def read_pleaf_data(payload):
    return {
        "pressure": to_mmH2O(payload[0]),
        "temp_sens": to_celsius(payload[1]),
        "temp_ext1": to_celsius(payload[2]),
        "temp_ext2": to_celsius(payload[3])
    }