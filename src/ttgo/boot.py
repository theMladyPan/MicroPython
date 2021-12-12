# This file is executed on every boot (including wake-boot from deepsleep)


#import webrepl

#webrepl.start()

import network, machine, ntptime, st7789, gc, esp, time, struct
from st7789 import color565, sysfont

from machine import RTC, ADC, Pin, SPI, UART, Timer
from config import ssid, password
from utils import wifi_list, clock

def mhz(n):
  return n*10**6

BL_Pin = 4     #backlight pin
SCLK_Pin = 18  #clock pin
MOSI_Pin = 19  #mosi pin
MISO_Pin = 2   #miso pin

RESET_Pin = 23 #reset pin
DC_Pin = 16    #data/command pin
CS_Pin = 5     #chip select pin

Button1_Pin = 35; #right button
Button2_Pin = 0;  #left button
TX_EN_Pin = 17;
TX_Pin = 21;
RX_Pin = 22;

HORIZONTAL = 5
VERTICAL=0

MODE=HORIZONTAL

def reset(p):
  display.fill(0)  


def message(text="", x=0, y=0, size=1, clear=False):
  if clear:
    display.fill(0)
  display.text((x, y), text, st7789.WHITE, sysfont, size, nowrap=False)
    

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


def request(p):
  uart1.write()

  
machine.freq(mhz(240))
esp.osdebug(0)

print("Mem free:", gc.mem_free())

button1 = Pin(Button1_Pin, Pin.IN, Pin.PULL_UP)
button2 = Pin(Button2_Pin, Pin.IN, Pin.PULL_UP)

BLK = Pin(BL_Pin, Pin.OUT)
spi = SPI(baudrate=40000000, miso=Pin(MISO_Pin), mosi=Pin(MOSI_Pin, Pin.OUT), sck=Pin(SCLK_Pin, Pin.OUT))
display = st7789.ST7789(spi, 240, 135, cs=Pin(CS_Pin), dc=Pin(DC_Pin), rst=None, xstart=40, ystart=53   ) # 135/240

# init display
display._set_mem_access_mode(MODE, False, False, False)
display.fill(0) #filling the display with black
BLK.value(1) #turn backlight on
display._set_mem_access_mode(MODE, False, False, True) #setting screen orientation (rotation (0-7), vertical mirror, horizonatal mirror, is bgr)


# bind button interrupts
#button1.irq(trigger=Pin.IRQ_FALLING, handler=wifi_list) #interrupt for right button (button 2)
button2.irq(trigger=Pin.IRQ_FALLING, handler=reset) #interrupt for right button (button 2)


uart1 = UART(1, baudrate=115200, tx=TX_Pin, rx=RX_Pin, timeout=500, timeout_char=1)

TX_EN = Pin(TX_EN_Pin, Pin.OUT)

tim1 = Timer(1)
#tim1.init(period=1000, mode=Timer.PERIODIC, callback=request)

while(1):
  b = bytearray()
  b.append(0x01)
  b.append(0x05)
  b.append(0x00)
  b.append(0x1F)
  b.append(0xDB)

  #enable RS485 for transmit
  TX_EN.on()
  n = uart1.write(b)  # write 5 bytes
  time.sleep_us(350)
  TX_EN.off()
  #message("Sent: "+str(n), clear=True, size=2)
  
  header_buf = bytearray(1)
  uart1.readinto(header_buf)
  if(header_buf[0]!=0x01):
    print("Invalid header: ", header_buf)
  else:
    len_buf = bytearray(1)
    uart1.readinto(len_buf)
    msg = bytearray(len_buf[0]-2)
    uart1.readinto(msg) 
    crc_buf = bytearray(1)
    uart1.readinto(crc_buf)

    chksum = header_buf[0] + len_buf[0] + crc_buf[0]
    for i in msg:
        chksum += int(i)
    
    print("CRC: ", chksum, chksum&0xFF)

    print("msg", msg)

    message("id: "+str(struct.unpack("!L", msg[3:7])[0]), y=24, size=2, clear=True)
    message("p: "+str(struct.unpack("!L", msg[7:11])[0])+" ubar", y=48, size=2)
    message("t: "+str((struct.unpack("!L", msg[11:15])[0]-272150)/1000)+" oC", y=72, size=2)
  while(button1.value()):
    pass

#message("Connecting to: "+ssid)
#do_connect()
#message("Connected", y=11)
#message("IP: "+str(wait_for_wifi()[0]), y=22)
#setDateTime()
#time.sleep(1)
#clock(display, 111, 5)