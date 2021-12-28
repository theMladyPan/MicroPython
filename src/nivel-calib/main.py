# This is your main script.# This file is executed on every boot (including wake-boot from deepsleep)


#import webrepl

#webrepl.start()

import network, machine, ntptime, gc, esp, time

from machine import RTC, ADC, Pin, SPI, UART, Timer
import config

def mhz(n):
  return n*10**6


def do_connect(block=False):
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  if not wlan.isconnected():
    wlan.connect(config.ssid, config.password)
    while block and not wlan.isconnected():
      pass
  return wlan
  

def wait_for_wifi():
  wlan = network.WLAN(network.STA_IF)
  while not wlan.isconnected():
    pass
  return wlan.ifconfig()

    
def setDateTime():
  rtc=RTC()
  ntptime.settime() # set the rtc datetime from the remote server
  return rtc.datetime()


def init_adc():
  ch_xyz = [a32, a33, a39] = [ADC(Pin(i)) for i in [32, 33, 39]]
  for axis in ch_xyz:
    axis.atten(ADC.ATTN_11DB) # 0-3.6V
    
  cur = [a.read() for a in ch_xyz]
  min = list(cur)
  max = list(cur)


machine.freq(mhz(240))
esp.osdebug(0)

print("Mem free:", gc.mem_free())

# bind button interrupts
# button1.irq(trigger=Pin.IRQ_FALLING, handler=wifi_list) #interrupt for right button (button 2)
# button2.irq(trigger=Pin.IRQ_FALLING, handler=reset) #interrupt for right button (button 2)

# uart1 = UART(1, baudrate=115200, tx=21, rx=22, timeout=100, timeout_char=5)


# tim1 = Timer(1)
# tim1.init(period=1000, mode=Timer.PERIODIC, callback=request)


class Stepper:
  def __init__(self, A, _A, B, _B):
    self.A = Pin(A, Pin.OUT)
    self.B = Pin(B, Pin.OUT)
    self.C = Pin(_A, Pin.OUT)
    self.D = Pin(_B, Pin.OUT)
    self.pins = [
      self.A, 
      self.B, 
      self.C, 
      self.D
    ]

    self.reg = 0b0001
    self.update()
  
  def __del__(self):
    for pin in self.pins:
      pin.init(mode=Pin.IN, pull=Pin.PULL_HOLD) # disable internal pull-up resistor

  def update(self):
    for i in range(4):
      self.pins[i].value((self.reg & (1 << i)) >> i)
  
  def fwd(self, sleep_us=None):
    if   self.reg == 0b0001: self.reg = 0b0011
    elif self.reg == 0b0010: self.reg = 0b0110
    elif self.reg == 0b0100: self.reg = 0b1100
    elif self.reg == 0b1000: self.reg = 0b1001

    elif self.reg == 0b0011: self.reg = 0b0010
    elif self.reg == 0b0110: self.reg = 0b0100
    elif self.reg == 0b1100: self.reg = 0b1000
    elif self.reg == 0b1001: self.reg = 0b0001

    self.update()
    if sleep_us:
      time.sleep_us(sleep_us)
  
  def rev(self, sleep_us=None):
    if   self.reg == 0b0001: self.reg = 0b1001
    elif self.reg == 0b0010: self.reg = 0b0011
    elif self.reg == 0b0100: self.reg = 0b0110
    elif self.reg == 0b1000: self.reg = 0b1100

    elif self.reg == 0b0011: self.reg = 0b0001
    elif self.reg == 0b0110: self.reg = 0b0010
    elif self.reg == 0b1100: self.reg = 0b0100
    elif self.reg == 0b1001: self.reg = 0b1000

    self.update()
    if sleep_us:
      time.sleep_us(sleep_us)

  def ffwd(self, steps, sleep_us):
    for i in range(steps):
      self.fwd(sleep_us)

  def frev(self, steps, sleep_us):
    for i in range(steps):
      self.rev(sleep_us)


# wlan = do_connect(block=True)
# print(f"connected to {wlan.ifconfig()}")
# setDateTime()

led_OR = Pin(4, Pin.OUT)
led_OR(1)
time.sleep(5)
# create motor on pins A, Ainv, B, Binv = 25, 26, 32, 33
#mot1 = Stepper(26,25,33,32)
#mot1.ffwd(400, 1000)
#mot1.frev(400, 1000)
led_OR(0)
machine.deepsleep(5000)
