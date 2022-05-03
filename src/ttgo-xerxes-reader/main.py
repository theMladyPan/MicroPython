# This file is executed on every boot (including wake-boot from deepsleep)


import machine, gc, esp, time

from machine import RTC, ADC, Pin, SPI, UART, Timer
from config import my_addr, TX_EN_Pin
from ttgo_config import *
from xerxes import send_msg, read_msg, read_pleaf_data, read_raw
 
# display imports
import st7789
import vga1_8x16 as font_small
import vga1_16x32 as font_big


def mhz(n):
  return n*10**6

machine.freq(mhz(240))
esp.osdebug(0)


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
    if big:
        v_offset += 30
    else:
        v_offset += 15
    

uart1 = None

def netscan():
    display.fill(0)
    netscan_flag.unset()       
    xoff = 0
    yoff = 0
    leaves = []
    for i in range(1, 128):
        send_msg(uart1, my_addr, i.to_bytes(1, "big"), b"")  # write empty payload
        time.sleep_ms(5)
        if uart1.any():
            reply = read_raw(uart1, timeout=0.005)     
            if reply:  
                leaves.append(reply["source"])
                message("#", big=False, x=xoff, y=yoff)
        else:
            message("-", big=False, x=xoff, y=yoff)   
        
        xoff += 10
        if i % 24 == 0:
            xoff = 0
            yoff += 20
            
    if len(leaves)>0:
        print("Found: ")
        print(", ".join(leaves))
        message(", ".join(leaves), clear=True)
        message("Continue?    ->", y=100)
        while button2():
            # wait for button press
            pass
        while not button2():
            pass  # debounce
        time.sleep_ms(10)
    else:
        print("Nothing found.")          
    
    display.fill(0)
    return leaves


def read_all_leaves(leaves):     
    avg_of = 100
    message("Reading ...", clear=True)
    # debounce   
    time.sleep_ms(30)  
    while not button1():
        time.sleep_ms(30)  
    
    while button1():
        for i in leaves:            
            p, ts, t1, t2, delitel = 0, 0, 0, 0, 0
            for k in range(avg_of):
                send_msg(uart1, my_addr, int(i).to_bytes(1, "big"), b"")  # write empty payload
                time.sleep(0.005)
                if uart1.any():
                    try:
                        reply = read_msg(uart1, timeout=0.005)    
                    except RuntimeError:
                        # read out rest of broken message
                        print("Error rcvd: ")
                        print(uart1.read())
                        continue
                    except ValueError:
                        print("Invalid checksum received")
                        continue
                    
                    if reply:
                        readings = read_pleaf_data(reply["payload"])
                        p  += readings["pressure"]
                        ts += readings["temp_sens"]
                        t1 += readings["temp_ext1"]
                        t2 += readings ["temp_ext2"]
                        delitel += 1
                    
            if delitel > 0:
                p /= delitel
                ts /= delitel
                t1 /= delitel
                t2 /= delitel
            
                multiline(
                    i + 
                    "\np:   %.3f mm" % p +
                    "\nts:  %.1f oC" % ts + 
                    "\nte1: %.1f oC" % t1 + 
                    "\nte2: %.1f oC" % t2,
                    clear=True,
                )
            else:
                multiline("No data rcvd.\nBroken cable?", clear=True)

    message("Release...", clear=True)
    while not button1():
        time.sleep_ms(30)  

def read_all_int(pin=None):
    print("starting reading...")
    read_all_flag.set()
    message("Searching...", clear=True)


def netscan_int(pin=None):
    netscan_flag.set()      

print("Mem free:", gc.mem_free())

button1 = Pin(Button1_Pin, Pin.IN, Pin.PULL_UP)
button2 = Pin(Button2_Pin, Pin.IN, Pin.PULL_UP)
tx_en = Pin(TX_EN_Pin, Pin.OUT, value=0)

# bind button interrupts
# button1.irq(trigger=Pin.IRQ_FALLING, handler=read_all_int) #interrupt for right button (button 1)
# button2.irq(trigger=Pin.IRQ_FALLING, handler=netscan_int) #interrupt for left button (button 2)

read_all_flag = Flag()
netscan_flag = Flag()
uart1 = UART(1, baudrate=115200, tx=22, rx=21, timeout=5, timeout_char=5)

# tim1 = Timer(1)
#tim1.init(period=1000, mode=Timer.PERIODIC, callback=request)

leaves = []

while 1: 
    if not button1():
        read_all_leaves(leaves)
    elif not button2():
        leaves = netscan()
    else:
        message("P sensors    ->")
        message("Netscan      ->", y=100)
        
    