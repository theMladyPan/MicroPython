

# This file is executed on every boot (including wake-boot from deepsleep)

#import esp

#esp.osdebug(None)

#import webrepl

#webrepl.start()

import os, network, machine, ntptime, time, st7789, math, gc, esp
from st7789 import color565
from machine import RTC, ADC, Pin
from ttgo import ttgo_init, display, clock, wifi_list, message, snake, display
import time

def mhz(n):
  return n*10**6
  
machine.freq(mhz(240))
esp.osdebug(0)
print(gc.mem_free())


def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('Kal-el', 'superman')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    
def setDateTime():
  rtc=RTC()
  ntptime.settime() # set the rtc datetime from the remote server
  rtc.datetime()
    
ttgo_init()
message(text="Scanning WLAN SSIDs ...")
ch_xyz = [a32, a33, a39] = [ADC(Pin(i)) for i in [32, 33, 39]]
for axis in ch_xyz:
  axis.atten(ADC.ATTN_11DB)
  
cur = [a.read() for a in ch_xyz]
min = list(cur)
max = list(cur)

Button1_Pin = 35; #right button
Button2_Pin = 0;  #left button
button1 = Pin(Button1_Pin, Pin.IN, Pin.PULL_UP)
button2 = Pin(Button2_Pin, Pin.IN, Pin.PULL_UP)

def calibrate(p):
  while not button1.value():
    last = [a.read() for a in ch_xyz]
    for i in range(3):
      if last[i] < min[i]:
        min[i] = last[i]
      elif last[i] > max[i]:
        max[i] = last[i]

def reset(p):
  display.fill(0)

button1.irq(trigger=Pin.IRQ_FALLING, handler=calibrate) #interrupt for right button (button 2)
button2.irq(trigger=Pin.IRQ_FALLING, handler=reset) #interrupt for right button (button 2)

def average(f, args=(), *, n):
  val = 0
  for i in range(n):
    val += f(*args)
  return val/n
  
class Pixel:
    def __init__(self, x=0, y=0, rgb=[0,0,0]):
      self.x = x
      self.y = y
      self.rgb = [self.r, self.g, self.b] = rgb
      
    def get_color(self):
      return color565(*tuple(self.rgb))
      
    def close_neighbours(self):
      x,y = self.x, self.y
      return [Pixel(xy[0], xy[1], [int(self.r*2/3), int(self.g*2/3), int(self.b*2/3)]) for xy in [(x, y-1), (x-1, y), (x+1, y), (x, y+1)]]
    
    def distant_neighbours(self):
      x,y = self.x, self.y
      return [Pixel(xy[0], xy[1], [int(self.r/3), int(self.g/3), int(self.b/3)]) for xy in [(x-1, y-1), (x-1, y+1), (x+1, y-1), (x+1, y+1)]]
      
    def neighbours(self):
      return self.close_neighbours()+self.distant_neighbours()
      
    def neighbourhood(self, n):
      nbhood = []
      for x in range(self.x-n, self.x+n+1):
        for y in range(self.y-n, self.y+n+1):
          d = math.sqrt((self.x-x)**2 + (self.y-y)**2)
          coeff = 1-(d/n)
          rgb = [int(c*coeff) if int(c*coeff) > 0 else 0 for c in [self.r, self.g, self.b]]
          nbhood.append(Pixel(x, y, rgb))
      return nbhood
      
    def show(self, display):
      if self.get_color():
        display.pixel(int(self.x), int(self.y), self.get_color())
      
    def blank(self, display, bg=0):
      display.pixel(int(self.x), int(self.y), bg)
    

pix = Pixel()
size = 10
n = 2

while False:
  last = [average(a.read, n=3) for a in ch_xyz]
  for i in range(3):
    try:
      cur[i] = float(last[i] - min[i])*100/(max[i] - min[i])
    except ZeroDivisionError:
     pass 
     
  last_pix = pix
  #last_pix.blank(display)
  #for p in last_pix.neighbourhood(size):
  #  p.blank(display)
  
  #pix = Pixel(int(display.width*cur[0]/100), int(display.height*cur[2]/100), [127, 0, 255])
  #pix.show(display)
  #for p in pix.neighbourhood(size):
  #  p.show(display)
  
  x,y=display.width - int(display.width*cur[0]/100), display.height - int(display.height*cur[2]/100)
  
  for xi in range(x-n, x+n+1):
    for yi in range(y-n, y+n+1):
      d = math.sqrt((x-xi)**2 + (y-yi)**2)
      coeff = 1-(d/n)
      rgb = [r,g,b] = [int(c*coeff) if int(c*coeff) > 0 else 0 for c in [50,196,255]]
      if r or g or b:

        display.pixel(xi, yi, color565(r, g, b))
  
  #message(text="%, ".join([str(i) for i in cur]))
do_connect()
setDateTime()

#snake()
#wifi_list()
#time.sleep(5)
clock()

