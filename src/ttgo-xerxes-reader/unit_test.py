
from dataclasses import dataclass
from statistics import mean, median, stdev
import time
import serial, struct


my_addr = b"\x00"

def b2i(data: bytes) -> int:
    return int(data.hex(), 16)


def s2b(data: int) -> bytes:
    return data.to_bytes(1, "big")


def checksum(message: bytes) -> bytes:
    summary = sum(message)
    summary ^= 0xFF  # get complement of summary
    summary += 1  # get 2's complement
    summary %= 0x100  # get last 8 bits of summary
    return summary.to_bytes(1, "big")


def send_msg(com: serial.Serial, destination: bytes, payload: bytes) -> None:    
    SOH = b"\x01"

    msg = SOH  # SOH
    msg += (len(payload) + 5).to_bytes(1, "big")  # LEN
    msg += my_addr
    msg += destination #  DST
    msg += payload
    msg += checksum(msg)
    com.write(msg)


@dataclass
class XerxesMessage:
    source: bytes
    destination: bytes
    length: int
    message_id: int
    payload: bytes


class XerxesLeaf:
    def __init__(self, address: int, serial_port: serial.Serial) -> None:
        self.com = serial_port
        self.addr = address

    
    def read(self) -> bytes:
        send_msg(self.com, self.addr.to_bytes(1, "big"), MsgId.fetch)
        rpl = read_msg(self.com)
        return rpl.payload, rpl.message_id
    

class PressureLeaf(XerxesLeaf):
    def read(self) -> list:
        pl, msgid = super().read()
        p, ts, te1, te2 = struct.unpack("!IIII", pl)
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
        x, y, te1, te2 = struct.unpack("!IIII", pl)
        return [x, y, te1, te2], msgid


def leaf_generator(devId: int, address: int, serial_port: serial.Serial) -> XerxesLeaf:
    #define DEVID_PRESSURE_600MBAR_2TEMP    0x03
    #define DEVID_PRESSURE_60MBAR_2TEMP     0x04    
    #define DEVID_STRAIN_24BIT_2TEMP        0x05

    if isinstance(devId, bytes):
        devId = b2i(devId)

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
        

def read_msg(com: serial.Serial) -> XerxesMessage:
    # wait for start of message
    next_byte = com.read(1)
    while next_byte != b"\x01":
        next_byte = com.read(1)
        if len(next_byte)==0:
            raise TimeoutError("No message in queue")

    checksum = 0x01
    # read message length
    msg_len = int(com.read(1).hex(), 16)
    checksum += msg_len

    #read source and destination address
    src = com.read(1)
    dst = com.read(1)

    for i in [src, dst]:
        checksum += int(i.hex(), 16) 

    # read message ID
    msg_id_raw = com.read(2)
    if(len(msg_id_raw)!=2):
        raise IOError("Invalid message received")
    for i in msg_id_raw:
        checksum += i

    msg_id = struct.unpack("!H", msg_id_raw)[0]

    # read and unpack all data into array, assuming it is uint32_t, big-endian
    raw_msg = bytes(0)
    for i in range(int(msg_len -    7)):
        next_byte = com.read(1)
        raw_msg += next_byte
        checksum += int(next_byte.hex(), 16)
    
    #read checksum
    rcvd_chks = com.read(1)
    checksum += int(rcvd_chks.hex(), 16)
    checksum %= 0x100
    if checksum:
        raise IOError("Invalid checksum received")

    return XerxesMessage(
        source=src,
        destination=dst,
        length=msg_len,
        message_id=msg_id,
        payload=raw_msg
    )


class MsgId:
    ping_req = struct.pack("!H", 0x0000)
    ping_reply = struct.pack("!H", 0x0001)
    ack_ok = struct.pack("!H", 0x0002)
    ack_nok = struct.pack("!H", 0x0003)
    fetch = struct.pack("!H", 0x0100)


if __name__ == "__main__":
    try:
        com = serial.Serial()
        com.port = "/dev/ttyUSB0"
        com.baudrate=115200
        com.timeout = 0.010

        com.open()

        leaves = []
        addresses = list(range(1, 32))

        dleaf = leaf_generator(
            devId=0x11,
            address=30,
            serial_port=com
        )
        distances = []

        for i in range(1000):
            distances.append(
                dleaf.read()[0][0]
            )

        print(
            mean(distances),
            median(distances),
            stdev(distances),
            (stdev(distances) / mean(distances)) * 100
        )
        
        while addresses:
            addr = addresses.pop()
            send_msg(com, addr.to_bytes(1, "big"), MsgId.ping_req)
            try:
                rpl = read_msg(com)
                leaves.append(
                    leaf_generator(
                        devId=rpl.payload,
                        address=addr,
                        serial_port=com
                    )
                )
                print(f"{rpl.source} replied. Adding: {leaves[-1]}")
            except TimeoutError:
                pass
            except IOError:
                addresses.append(addr)

        while 1:
            for leaf in leaves:
                try:
                    reading = leaf.read()
                    print(f"{leaf.addr} replied with: {reading[0]}, msgid: {hex(reading[1])}.")
                except TimeoutError:
                    print(f"{leaf.addr} timeouted...")
                except IOError:
                    pass
                except ValueError:
                    pass
            time.sleep(1)
            

    finally:
        com.close()