# This file is executed on every boot (including wake-boot from deepsleep)


#import webrepl

#webrepl.start()

import network, machine, ntptime, st7789, gc, esp, time
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
button1.irq(trigger=Pin.IRQ_FALLING, handler=wifi_list) #interrupt for right button (button 2)
button2.irq(trigger=Pin.IRQ_FALLING, handler=reset) #interrupt for right button (button 2)


uart1 = UART(1, baudrate=115200, tx=21, rx=22, timeout=100, timeout_char=5)


tim1 = Timer(1)
#tim1.init(period=1000, mode=Timer.PERIODIC, callback=request)

while(1):
  b = bytearray()
  b.append(0x01)
  b.append(0x05)
  b.append(0x00)
  b.append(0x1F)
  b.append(0xDB)
  uart1.write(b)  # write 5 bytes
  
  m = uart1.read()         # read up to 5 bytes
  message("Received: "+str(m), size=3, clear=True)
  time.sleep(1)

#message("Connecting to: "+ssid)
#do_connect()
#message("Connected", y=11)
#message("IP: "+str(wait_for_wifi()[0]), y=22)
#setDateTime()
#time.sleep(1)
#clock(display, 111, 5)