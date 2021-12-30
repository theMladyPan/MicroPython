import network, machine, ntptime, gc, esp, time, config
import uos as os
from machine import RTC, ADC, Pin, SPI, TouchPad


machine.freq(240*10**6)
esp.osdebug(0)

print("RAM free kiB:", gc.mem_free())
s = os.statvfs(".")
print("Mem freeMiB:", s[0]*s[3]/2**20)

# bind button interrupts
# button1.irq(trigger=Pin.IRQ_FALLING, handler=wifi_list) #interrupt for right button (button 2)
# button2.irq(trigger=Pin.IRQ_FALLING, handler=reset) #interrupt for right button (button 2)

# uart1 = UART(1, baudrate=115200, tx=21, rx=22, timeout=100, timeout_char=5)


# tim1 = Timer(1)
# tim1.init(period=1000, mode=Timer.PERIODIC, callback=request)

mm=50.1
led = Pin(2, Pin.OUT)
# time.sleep(5)
# create motor on pins A, Ainv, B, Binv = 25, 26, 32, 33
hspi = SPI(1, 500000, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
cs = Pin(27, mode=Pin.OUT, value=1) # cs pin, high = deselected, low=selected

touch4 = TouchPad(Pin(4))
touch15 = TouchPad(Pin(15))


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

  def __call__(self, steps, sleep_us):
    if steps>0:
      self.ffwd(steps, sleep_us)
    elif steps<0:
      self.frev(abs(steps), sleep_us)
    else:
      pass


def readVals(spi, cs, average_of=1): 

  VALmin = 1638.0 # counts = 10% 2^14
  VALmax = 14745.0 # counts = 90% 2^14
  Pmin = 0.0 # mbar
  Pmax = 60.0 # mbar, or: 611.8298 mm

  temp = 0
  pressure = 0

  rxdata = bytearray(4)
  led(1)

  for i in range(average_of):
    try:
      cs(0)                               # Select peripheral.
      spi.readinto(rxdata, 0x00)          # Read 8 bytes inplace while writing 0x42 for each byte.
    finally:
      cs(1)  

    b0 = rxdata[0]
    b1 = rxdata[1]
    t0 = rxdata[2]
    t1 = rxdata[3]

    status = b0 & 0b11000000;
    pval = ((b0 & 0b00111111)<<8) + b1;
    t = ((t0<<8) + (t1 & 0b11111000))>>5;

    temp += (t*200.0/2047.0)-50.0
    pressure += (((pval-VALmin)*(Pmax-Pmin))/(VALmax-VALmin)) + Pmin
    time.sleep_us(500)

  led(0)
  temp/=average_of
  pressure/=average_of
  # pressure = (11.2*pressure) - (.0308*(pressure**2))
  # fit = 11,2x + -0,0308x^2, R2=1

  return temp, pressure


def cycles(n=10, step=mm, speed=1500, sleep_ms=100, average=100, filename="default.csv"):
  f = open(filename, "w")

  for i in range(n): 
    m(-step, speed)
    time.sleep_ms(sleep_ms)
    t, p = readVals(hspi,cs,average)
    vals = ";".join([str(i+1), str(p).replace(".",","), str(t).replace(".",",")])
    print(vals)
    f.write(vals + "\n")
  for i in range(n): 
    m(step, speed)
    time.sleep_ms(sleep_ms)
    t, p = readVals(hspi,cs,average)
    vals = ";".join([str(n-i-1), str(p).replace(".",","), str(t).replace(".",",")])
    print(vals)
    f.write(vals + "\n")
  f.close()
  
def blink(n):
    for i in range(n):        
        led(1)
        time.sleep_ms(100)
        led(0)
        time.sleep_ms(100)

# wlan = do_connect(block=True)
# print(f"connected to {wlan.ifconfig()}")
# setDateTime()

m = Stepper(26,25,33,32)
blink(3)

while 1:
    if touch4.read()<256:
        cycles(n=20, sleep_ms=100, average=100, filename="rychle.csv")
    if touch15.read()<256:
        cycles(n=200, sleep_ms=10000, average=1000, filename="pomale.csv")