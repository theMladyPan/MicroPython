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
