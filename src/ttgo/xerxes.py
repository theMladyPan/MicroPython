import struct


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
        # activate transmission mode
        tx_en.on()

    com.write(msg)

    if tx_en:
        # deactivate transmission mode
        tx_en.off()
    #time.sleep(0.001)
    #com.write(os.urandom(128))

def read_msg(com):
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

    sot = com.read(1)

    for i in [src, dst, sot]:
        checksum += int(i.hex(), 16) 

    # read message ID
    msg_id_raw = com.read(4)
    if(len(msg_id_raw)!=4):
        raise IOError("Invalid message received")
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
    checksum += int(rcvd_chks.hex(), 16)
    checksum %= 0x100
    if checksum:
        raise IOError("Invalid checksum received")

    return {
        "source": src,
        "destination": dst,
        "length": msg_len,
        "message_id": msg_id,
        "payload": msg_array 
        }