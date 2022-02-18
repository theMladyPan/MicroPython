# This file is executed on every boot (including wake-boot from deepsleep)


#import webrepl

#webrepl.start()


import network, machine, ntptime, st7789, gc, esp, time
from st7789 import color565, sysfont

from machine import RTC, ADC, Pin, SPI, UART, Timer
from config import ssid, password, my_addr, TX_EN_Pin
from utils import wifi_list
from xerxes import send_msg, read_msg, read_pleaf_data, read_raw

def mhz(n):
  return n*10**6

machine.freq(mhz(240))
esp.osdebug(0)

BL_Pin = 4     #backlight pin
SCLK_Pin = 18  #clock pin
MOSI_Pin = 19  #mosi pin
MISO_Pin = 2   #miso pin

RESET_Pin = 23 #reset pin
DC_Pin = 16    #data/command pin
CS_Pin = 5     #chip select pin

Button1_Pin = 35; #right button
Button2_Pin = 0;  #left button
HORIZONTAL = 5
VERTICAL=0


MODE=HORIZONTAL

def reset(p):
  display.fill(0)  

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

def message(text="", x=0, y=0, size=1, clear=False):
  if clear:
    display.fill(0)
  display.text((x, y), text, st7789.WHITE, sysfont, size, nowrap=False)
  
def multiline(text="", x=0, y=0, size=1, clear=False):
  if clear:
    display.fill(0)
  v_offset = y
  for i in text.split("\n"):
    message(i, x=x, y=v_offset, size=size, clear=False)
    v_offset += size*9
    

def do_connect(block=False):
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  if not wlan.isconnected():
    wlan.connect(ssid, password)
    while block and not wlan.isconnected():
      pass
  

def wait_for_wifi():
  wlan = network.WLAN(network.STA_IF)
  while not wlan.isconnected():
    pass
  return wlan.ifconfig()

    
def setDateTime():
  rtc=RTC()
  ntptime.settime() # set the rtc datetime from the remote server
  rtc.datetime()


def init_adc():
  ch_xyz = [a32, a33, a39] = [ADC(Pin(i)) for i in [32, 33, 39]]
  for axis in ch_xyz:
    axis.atten(ADC.ATTN_11DB) # 0-3.6V
    
  cur = [a.read() for a in ch_xyz]
  min = list(cur)
  max = list(cur)


def calibrate(p):
  while not button1.value():
    last = [a.read() for a in ch_xyz]
    for i in range(3):
      if last[i] < min[i]:
        min[i] = last[i]
      elif last[i] > max[i]:
        max[i] = last[i]
        
uart1=None

def netscan():
  leaves = []
  for i in range(1, 255):
    send_msg(uart1, my_addr, i.to_bytes(1, "big"), b"")  # write empty payload
    time.sleep(0.005)
    if uart1.any():
        reply = read_raw(uart1, timeout=0.005)       
        leaves.append(reply["source"])
  print("Found: ")
  print(", ".join(leaves))
  message(", ".join(leaves), size=2, clear=True)
  
def read_all_leaves():         
    for i in range(1, 255):
        send_msg(uart1, my_addr, i.to_bytes(1, "big"), b"")  # write empty payload
        time.sleep(0.005)
        if uart1.any():
            try:
                reply = read_msg(uart1, timeout=0.005)    
            except RuntimeError:
                # read out rest of broken message
                uart1.read()
                continue
            
            print(reply)
            readings = read_pleaf_data(reply["payload"])
            
            multiline(
                reply["source"] + 
                "\np: %.2f mm" % readings["pressure"] +
                "\nts: %.2f oC" % readings["temp_sens"] + 
                "\nte1: %.2f oC" % readings["temp_ext1"] + 
                "\nte2: %.2f oC" % readings ["temp_ext2"],
                clear=True,
                size=3
            )
        
def read_all_int(pin=None):
    print("starting reading...")
    read_all_flag.set()

def netscan_int(pin=None):
    netscan_flag.set()       
    
print("Mem free:", gc.mem_free())

button1 = Pin(Button1_Pin, Pin.IN, Pin.PULL_UP)
button2 = Pin(Button2_Pin, Pin.IN, Pin.PULL_UP)
tx_en = Pin(TX_EN_Pin, Pin.OUT, value=0)

BLK = Pin(BL_Pin, Pin.OUT)
spi = SPI(baudrate=40000000, miso=Pin(MISO_Pin), mosi=Pin(MOSI_Pin, Pin.OUT), sck=Pin(SCLK_Pin, Pin.OUT))
display = st7789.ST7789(spi, 240, 135, cs=Pin(CS_Pin), dc=Pin(DC_Pin), rst=None, xstart=40, ystart=53   ) # 135/240

# init display
display._set_mem_access_mode(MODE, False, False, False)
display.fill(0) #filling the display with black
BLK.value(1) #turn backlight on
display._set_mem_access_mode(MODE, False, False, True) #setting screen orientation (rotation (0-7), vertical mirror, horizonatal mirror, is bgr)

# bind button interrupts
button1.irq(trigger=Pin.IRQ_FALLING, handler=read_all_int) #interrupt for right button (button 1)
button2.irq(trigger=Pin.IRQ_FALLING, handler=netscan_int) #interrupt for left button (button 2)

read_all_flag = Flag()
netscan_flag = Flag()
uart1 = UART(1, baudrate=115200, tx=22, rx=21, timeout=5, timeout_char=5)

# tim1 = Timer(1)
#tim1.init(period=1000, mode=Timer.PERIODIC, callback=request)

message("P sensors   ->", size=3)
message("Netscan     ->", size=3, y=100)

while 1: 
    if read_all_flag.is_set():
        read_all_leaves()
    elif netscan_flag.is_set():
        netscan()
    time.sleep(0.1)
  # m = uart1.read()         # read up to 5 bytes
  # message(str(m), size=1, clear=True)
  # time.sleep(2)

#message("Connecting to: "+ssid)
#do_connect()
#message("Connected", y=11)
#message("IP: "+str(wait_for_wifi()[0]), y=22)
#setDateTime()
#time.sleep(1)
#clock(display, 111, 5)