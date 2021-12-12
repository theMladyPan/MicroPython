


import random #for random number generation (like random color)
import st7789 #for display
import time #mostly fro sleep
from machine import Pin, SPI # for display and buttons
import math #math for pi value
from sysfont import sysfont #sysfont for drawing text
import network


BL_Pin = 4     #backlight pin
SCLK_Pin = 18  #clock pin
MOSI_Pin = 19  #mosi pin
MISO_Pin = 2   #miso pin

RESET_Pin = 23 #reset pin
DC_Pin = 16    #data/command pin
CS_Pin = 5     #chip select pin

Button1_Pin = 35; #right button
Button2_Pin = 0;  #left button
button1 = Pin(Button1_Pin, Pin.IN, Pin.PULL_UP)
button2 = Pin(Button2_Pin, Pin.IN, Pin.PULL_UP)


def callback_b1(p):
    clear_screen()

def callback_b2(p):
    fill_random_color()

button1.irq(trigger=Pin.IRQ_FALLING, handler=callback_b1) #interrupt for right button (button 2)
button2.irq(trigger=Pin.IRQ_FALLING, handler=callback_b2) #interrupt for left button (button 1)

BLK = Pin(BL_Pin, Pin.OUT)
spi = SPI(baudrate=40000000, miso=Pin(MISO_Pin), mosi=Pin(MOSI_Pin, Pin.OUT), sck=Pin(SCLK_Pin, Pin.OUT))
display = st7789.ST7789(spi, 135, 240, cs=Pin(CS_Pin), dc=Pin(DC_Pin), rst=None)


def clear_screen():
    display._set_mem_access_mode(0, False, False, False)
    display.fill(0) #filling the display with black

def fill_random_color():
    fill_hline()
    fill_vline()
    display.fill(random_color())
    display._set_mem_access_mode(0, False, False, False)

def fill_hline():
    display._set_mem_access_mode(0, False, False, False)
    for i in range(0,240):
      display.hline(0, i, 65, st7789.color565(random.getrandbits(8),random.getrandbits(8),random.getrandbits(8)))


    display._set_mem_access_mode(1, False, False, False)
    for i in range(0,240):
      display.hline(0, i, 65, st7789.color565(random.getrandbits(8),random.getrandbits(8),random.getrandbits(8)))

    clear_screen()


def fill_vline():
    display._set_mem_access_mode(0, False, False, False)
    for i in range(0,135):
      display.vline(i, 0, 110, st7789.color565(random.getrandbits(8),random.getrandbits(8),random.getrandbits(8)))

    display._set_mem_access_mode(2, False, False, False)
    for i in range(0,135):
      display.vline(i, 0, 110, st7789.color565(random.getrandbits(8),random.getrandbits(8),random.getrandbits(8)))

    clear_screen()

def random_color():
    return st7789.color565(random.getrandbits(8),random.getrandbits(8),random.getrandbits(8))
    
def message(x=0, y=0, text="", size=2):
  display.fill(0)
  display.text((x, y), text, st7789.WHITE, sysfont, size, nowrap=False)
    
def wifi_list():
  wlan = network.WLAN(network.STA_IF)
  networks = wlan.scan()
  display.fill(0)
  display.text((0, 0), "WLAN list:", st7789.CYAN, sysfont, 2, nowrap=True)
  for i in range(0, len(networks)):
    ssid, signal = networks[i][0].decode("utf-8"), networks[i][3]
    if len(ssid)>13:
      ssid=ssid[0:10]+"..."
    if signal < -90:
      color=st7789.RED
    elif signal <-80:
      color=st7789.YELLOW
    else:
      color=st7789.GREEN
    display.text((0, i*9+20), ssid, color, sysfont, 1, nowrap=True)
    display.text((display.width-11*4, i*9+20), str(signal), color, sysfont, 1, nowrap=True)
    display.text((display.width-6*4, i*9+20), "dBm", color, sysfont, 1, nowrap=True)
    
def ttgo_init():
  clear_screen() #clear screen by filling black rectangle (slow)
  BLK.value(1) #turn backlight on
  display._set_mem_access_mode(0, False, False, True) #setting screen orientation (rotation (0-7), vertical mirror, horizonatal mirror, is bgr), False, False, True)

def clock(v=150):
  second, minute, hour = None, None, None
    
  v=display.height - 8*3
  display.fill_rectangle(0, v, display.width, 8*3, st7789.BLACK)
  

  while True:  
    curT=time.localtime()
    lastSecond, lastMinute, lastHour = second, minute, hour
    
    hour = ("0"+str(curT[3]+2)) if curT[3]<10 else str(curT[3]+2)
    minute = ("0"+str(curT[4])) if curT[4]<10 else str(curT[4])
    second = ("0"+str(curT[5])) if curT[5]<10 else str(curT[5])
    sTime = hour+":"+minute+":"+second
    if hour != lastHour:
      display.fill_rectangle(0,v, 5*3*3, 8*3, st7789.BLACK)
      display.text((0, v), hour, st7789.CYAN, sysfont, 3, nowrap=True)
    if minute != lastMinute:
      display.fill_rectangle(3*5*3,v, 5*3*3, 8*3, st7789.BLACK)
      display.text((3*5*3, v), minute, st7789.CYAN, sysfont, 3, nowrap=True)
      
    if second != lastSecond:
      display.fill_rectangle(6*5*3,v, 5*3*3, 8*3, st7789.BLACK)
      display.text((6*5*3, v), second, st7789.CYAN, sysfont, 3, nowrap=True)
      
    display.text((0, v), "  :  :", st7789.RED, sysfont, 3, nowrap=True)
    
def main2():
    clear_screen() #clear screen by filling black rectangle (slow)
    BLK.value(1) #turn backlight on
    display._set_mem_access_mode(0, False, False, True) #setting screen orientation (rotation (0-7), vertical mirror, horizonatal mirror, is bgr)



    while True:
      clear_screen()
      BLK.value(1)
      if not button1.value():
          fill_hline()
      if not button2.value():
          fill_vline()

     #display.fill(st7789.BLACK)
     #display.pixel(random.randint(0, 135), random.randint(0, 240) , st7789.color565(random.getrandbits(8),random.getrandbits(8),random.getrandbits(8)))

      x = random.randint(0,135)
      y = random.randint(0,240)
      w = random.randint(0,135)
      h = random.randint(0,240)
      display.circle(x,y,30,random_color())
      display.ellipse(x, y, 10, 20, random_color())


      clear_screen()
      time.sleep(1)

      clear_screen()

      display.hline(10, 127, 63, random_color())
      time.sleep(1)

      display.vline(10, 0, 127, random_color())
      time.sleep(1)

      display.fill_hrect(23, 50, 30, 75, random_color())
      time.sleep(1)

      display.hline(0, 0, 127, random_color())
      time.sleep(1)

      display.line(127, 0, 64, 127, random_color())
      time.sleep(2)

      clear_screen()

      coords = [[0, 63], [78, 80], [122, 92], [50, 50], [78, 15], [0, 63]]
      display.lines(coords, random_color())
      time.sleep(1)

      clear_screen()
      display.fill_polygon(7, 63, 63, 50, random_color())
      time.sleep(1)

      display.fill_rectangle(0, 0, 15, 127, random_color())
      time.sleep(1)

      clear_screen()

      display.fill_rectangle(0, 0, 63, 63, random_color())
      time.sleep(1)

      display.rectangle(0, 64, 63, 63, random_color())
      time.sleep(1)

      display.fill_rectangle(64, 0, 63, 63, random_color())
      time.sleep(1)

      display.polygon(3, 96, 96, 30, random_color(), rotate=15)
      time.sleep(3)


      clear_screen()

      display.fill_circle(32, 32, 30, random_color())
      time.sleep(1)

      display.circle(32, 96, 30, random_color())
      time.sleep(1)

      display.ellipse(96, 96, 16, 30, random_color())

      display.fill_ellipse(96, 32, 30, 16, random_color())
      time.sleep(1)




      display.fill(0);
      v = 30
      display.text((0, v), "Hello World!", random_color(), sysfont, 1, nowrap=True)
      v += sysfont["Height"]
      display.text((0, v), "Hello World!", random_color(), sysfont, 2, nowrap=True)
      v += sysfont["Height"] * 2
      display.text((0, v), "Hello World!", random_color(), sysfont, 3, nowrap=True)
      v += sysfont["Height"] * 3
      display.text((0, v), str(1234.567), random_color(), sysfont, 4, nowrap=True)
      time.sleep_ms(1500)
      display.fill(0);
      v = 0
      display.text((0, v), "Hello World!", random_color(), sysfont)
      v += sysfont["Height"]
      display.text((0, v), str(math.pi), random_color(), sysfont)
      v += sysfont["Height"]
      display.text((0, v), " Want pi?", random_color(), sysfont)
      v += sysfont["Height"] * 2
      display.text((0, v), hex(8675309), random_color(), sysfont)
      v += sysfont["Height"]
      display.text((0, v), " Print HEX!", random_color(), sysfont)
      v += sysfont["Height"] * 2
      display.text((0, v), "Sketch has been", random_color(), sysfont)
      v += sysfont["Height"]
      display.text((0, v), "running for: ", random_color(), sysfont)
      v += sysfont["Height"]
      display.text((0, v), str(time.ticks_ms() / 1000), random_color(), sysfont)
      v += sysfont["Height"]
      display.text((0, v), " seconds.", random_color(), sysfont)

      time.sleep(10)
      BLK.value(0)
      
def pixel(xy):
  display.pixel(int(xy[0]), int(xy[1]), xy[2])
  
def blank(xy):
  display.pixel(int(xy[0]), int(xy[1]), 0)
  
def snake():
  display.fill(0)
  [xvel, yvel] = [random.random()*2-1 for i in range(2)]
  xvelmax, yvelmax = 3,3
  x, y = 0, 0
  lastx, lasty = 0, 0
  pos = [(0, 0, random_color()) for i in range(150)]
  for p in pos:
    pixel(p)
  while 1:
    xvel += random.random()*2-1
    yvel += random.random()*2-1
    x+=xvel
    y+=yvel
    if x > display.width-1:
      xvel=-xvel
      x=display.width-1
    if x<0:
      xvel=-xvel
      x=0
    if y > display.height-1:
      yvel = -yvel
      y=display.height-1
    if y < 0:
      yvel = -yvel
      y=0
    if xvel < -xvelmax:
      xvel=-xvelmax
    if xvel > xvelmax:
      xvel = xvelmax
    if yvel < -yvelmax:
      yvel = -yvelmax
    if yvel > yvelmax:
      yvel = yvelmax
    pos.append((x,y, random_color()))
    pixel(pos[-1])
    blank(pos.pop(0))
