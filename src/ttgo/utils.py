import network, st7789, random, time
from st7789 import sysfont

      
def pixel(display, xy):
  display.pixel(int(xy[0]), int(xy[1]), xy[2])
  
def blank(display, xy):
  display.pixel(int(xy[0]), int(xy[1]), 0)
  

def wifi_list(display):
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  networks = wlan.scan()
  display.fill(0)
  display.text((0, 0), "WLAN list:", st7789.CYAN, sysfont, 1, nowrap=True)
  for i in range(0, len(networks)):
    ssid, signal = networks[i][0].decode("utf-8"), networks[i][3]
    if len(ssid)>13:
      ssid=ssid[0:20]+"..."
    if signal < -90:
      color=st7789.RED
    elif signal <-80:
      color=st7789.YELLOW
    else:
      color=st7789.GREEN
    display.text((0, i*9+20), ssid, color, sysfont, 1, nowrap=True)
    display.text((display.width-11*4, i*9+20), str(signal), color, sysfont, 1, nowrap=True)
    display.text((display.width-6*4, i*9+20), "dBm", color, sysfont, 1, nowrap=True)

def clock(display, v, size=3):
  second, minute, hour = None, None, None
    
  v=display.height - 8*size
  display.fill_rectangle(0, v, display.width, 8*size, st7789.BLACK)

  while True:  
    curT=time.localtime()
    lastSecond, lastMinute, lastHour = second, minute, hour
    
    hour = ("0"+str(curT[3]+2)) if curT[3]<10 else str(curT[3]+2)
    minute = ("0"+str(curT[4])) if curT[4]<10 else str(curT[4])
    second = ("0"+str(curT[5])) if curT[5]<10 else str(curT[5])
    sTime = hour+":"+minute+":"+second
    
    if hour != lastHour:
      display.fill_rectangle(0,v, 5*3*size, 8*size, st7789.BLACK)
      display.text((0, v), hour, st7789.CYAN, sysfont, size, nowrap=True)
    if minute != lastMinute:
      display.fill_rectangle(3*5*size,v, 5*3*size, 8*size, st7789.BLACK)
      display.text((3*5*size + 2, v), minute, st7789.CYAN, sysfont, size, nowrap=True)
      
    if second != lastSecond:
      display.fill_rectangle(6*5*size,v, 5*3*size, 8*size, st7789.BLACK)
      display.text((6*5*size + 4, v), second, st7789.CYAN, sysfont, size, nowrap=True)
      
    display.text((0, v), "  :  :", st7789.RED, sysfont, size, nowrap=True)


def random_color():
    return st7789.color565(random.getrandbits(8),random.getrandbits(8),random.getrandbits(8))
    
    
def snake(display):
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
    pixel(display, pos[-1])
    blank(display, pos.pop(0))
