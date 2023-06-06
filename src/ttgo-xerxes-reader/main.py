
import struct
import machine, gc, esp, time, math

from machine import Pin, SPI, UART, Timer
from config import my_addr, TX_EN_Pin
from ttgo_config import *
from xerxes import send_msg, read_msg, MsgId, c2b, b2c
from xerxes_leafs import leaf_generator
 
# display imports
import st7789
import vga1_8x16 as font_small
import vga1_16x32 as font_big


def mhz(n):
  return n*10**6

machine.freq(mhz(240))
esp.osdebug(0)


master_addr = b"\x00"


def stdev(data, xbar=None):
    if iter(data) is data:
        data = list(data)
    if xbar is None:
        xbar = sum(data)/len(data)
    total = total2 = 0
    for x in data:
        total += (x - xbar)**2
        total2 += (x - xbar) 
    total -= total2**2/len(data)
    return math.sqrt(total/(len(data) - 1))


spi = SPI(1, baudrate=30000000, sck=Pin(SCLK_Pin), mosi=Pin(MOSI_Pin))
display = st7789.ST7789(
    spi, 
    240, 
    135, 
    rotation=1, 
    rotations=ORIENTATIONS, 
    cs=Pin(CS_Pin, Pin.OUT), 
    reset=Pin(RESET_Pin, Pin.OUT), 
    dc=Pin(DC_Pin, Pin.OUT), 
    backlight=Pin(BL_Pin, Pin.OUT),	
)


display.init()
display.on()

display.jpg("rubint.jpg", 0, 0, st7789.FAST)

class Flag:
    def __init__(self, value=False):
        self.value = value
    
    def set(self):
        self.value = True
        
    def unset(self):
        self.value = False
        
    def toggle(self):
        self.value = not self.value
        
    def is_set(self):
        return self.value


def message(text="", x=0, y=0, big=True, clear=False, wrap=True):
    if clear:
        display.fill(0)
    if big:
        font = font_big
        cl = 15
        yo = 30
    else:
        font = font_small  
        cl = 30
        yo = 15
    if len(text) > cl and wrap:
        for i in range(len(text)/cl):
            display.text(font, text[i*cl : i * cl + 15], x, y)
            y += yo
            
    else:
        display.text(font, text, x, y)
  
  
def multiline(text, x=0, y=0, big=True, clear=False):
  if clear:
    display.fill(0)
  v_offset = y
  for i in text.split("\n"):
    message(i, x=x, y=v_offset, big=big)
    v_offset += 30 if big else 15
    

uart1 = None

def netscan():
  display.fill(0)
  netscan_flag.unset()
  xoff = 0
  yoff = 0
  leaves_addr = []
  leaves = []

  for i in range(1, 128):
    send_msg(
        uart1, 
        my_addr, 
        i.to_bytes(1, "little"), 
        MsgId.ping_req
    )  # write empty payload
    time.sleep_ms(5)
    if uart1.any():
      print("received reply")
      if reply := read_msg(uart1, timeout=15):
        print("Found: ", end="")
        print(f"DevId: {str(b2c(reply.payload))}, Addr: {str(b2c(reply.source))}")
        leaves_addr.append(str(struct.unpack("B", reply.source)[0]))
        new_leaf = leaf_generator(
                devId=b2c(reply.payload),
                address=b2c(reply.source),
                root_addr=b2c(my_addr),
                serial_port=uart1
            )
        leaves.append(
            new_leaf
        )
        print(f"Appending: {str(new_leaf)}")
        message("#", big=False, x=xoff, y=yoff)
    else:
      message("-", big=False, x=xoff, y=yoff)   

    xoff += 10
    if i % 24 == 0:
        xoff = 0
        yoff += 20

  if leaves:
    print("Found: ")
    print(", ".join(leaves_addr))
    message(", ".join(leaves_addr), clear=True)
    message("Continue?    ->", y=100)
  else:
    message("Nothing found. ", clear=True)
    message("Continue?    ->", y=100)
    print("Nothing found.")          

  while bot_btn():
      # wait for button press
      pass
  while not bot_btn():
      pass  # debounce
  time.sleep_ms(10)
  display.fill(0)
  return leaves


def read_all_int(pin=None):
    print("starting reading...")
    read_all_flag.set()
    message("Searching...", clear=True)


def netscan_int(pin=None):
    netscan_flag.set()      

print("Mem free:", gc.mem_free())

top_btn = Pin(Button1_Pin, Pin.IN, Pin.PULL_UP)
bot_btn = Pin(Button2_Pin, Pin.IN, Pin.PULL_UP)
tx_en = Pin(TX_EN_Pin, Pin.OUT, value=0)

# bind button interrupts
# top_btn.irq(trigger=Pin.IRQ_FALLING, handler=read_all_int) #interrupt for right button (button 1)
# bot_btn.irq(trigger=Pin.IRQ_FALLING, handler=netscan_int) #interrupt for left button (button 2)

read_all_flag = Flag()
netscan_flag = Flag()
uart1 = UART(1, baudrate=115200, tx=22, rx=21, timeout=5, timeout_char=5)

# tim1 = Timer(1)
# tim1.init(period=1000, mode=Timer.PERIODIC, callback=request)


time.sleep(.5)
display.fill(0)
leaves = []
while not leaves:
  leaves = netscan()

display.fill(0)
message("3 samples  ->")
message("10 samples ->", y=100)

while top_btn() and bot_btn(): ...

nr = 10 if top_btn() else 3
ts = 0

time.sleep_ms(100)

display.fill(0)
display.rotation(0)

while 1:        
  i = 0
  while leaves:
    leaf = leaves[i]
    readings = []
    try:
      message(
          text=f"{hex(leaf.addr)}: {bin(leaf.addr)}: {str(leaf.addr)}",
          big=False,
      )
      start = time.ticks_ms()

      for _ in range(nr):
        reading, msgid = leaf.read()
        readings.append(reading)
        if ts: time.sleep_ms(ts)

      end = time.ticks_ms()    

            # v1, v2, v3, v4 = [], [], [], []
      values = [[] for _ in range(len(readings[0]))]
      # print(readings)
      for reading in readings:  # 2D array
          for i_value in range(len(reading)):  
              values[i_value].append(reading[i_value])

      averages = [sum(value_list)/nr for value_list in values]
      print("Averages: ", averages)


      # av1, av2, av3, av4 = sum(v1)/nr, sum(v2)/nr, sum(v3)/nr, sum(v4)/nr
      # sd1, sd2, sd3, sd4 = stdev(v1), stdev(v2), stdev(v3), stdev(v4)

      # averages = [av1, av2, av3, av4]
      # deviations = [sd1, sd2, sd3, sd4]


      print(leaf.addr, "Averages: ", averages, "msgid: ", hex(msgid))
      # text = ", ".join(["{:4.3f}".format(i*1000) for i in averages])
      y=30
      for average in averages:
          display.text(font_small, "{:4.3f}".format(average), 0, y)
          y+= 18
      # text += ", ".join(["{:4.1f}".format(i) for i in [av3, av4]])
      # multiline(
      #     text=text,
      #     clear=False,
      #     big=False,
      #     y=35
      # )
      # message(
      #     text=", ".join(["{:4.4f}".format(i) for i in deviations]), 
      #     clear=False,
      #     big=False,
      #     y=70
      # )
      dt = (end - start)/1000
      fs = nr/dt
      message(
          text="Refresh: {:4.2f}Hz".format(fs),
          clear=False,
          big=False,
          y=220
      )


    except RuntimeError:
        print(leaf.addr, " timeouted...")

    if not top_btn():
        if i < len(leaves) - 1:
            i += 1
    elif not bot_btn():
        if i > 0:
            i -= 1
