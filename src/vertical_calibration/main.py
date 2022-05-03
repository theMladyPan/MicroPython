
from ttgo_config import *   
import gc, esp, time

from machine import RTC, ADC, Pin, SPI, UART, Timer, freq

# display imports
import st7789
import vga1_8x16 as font_small
import vga1_16x32 as font_big


def mhz(n):
  return n*10**6

freq(mhz(240))
esp.osdebug(0)
print("Mem free:", gc.mem_free())


class Counter:
    def __init__(self) -> None:
        self._ctr = 0
    
    
    def inc(self, val:int) -> None:
        self._ctr += val
    
    
    def dec(self, val:int) -> None:
        self._ctr -= val


    @property
    def value(self) -> int:
        return self._ctr
    
    
    @value.setter
    def value(self, val:int) -> None:
        self._ctr = val
        

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


class Stepper:
    "Assuming the order is A>C>B>D"
    def __init__(self, pin_a: Pin, pin_b: Pin, pin_c: Pin, pin_d: Pin, delay_us: int) -> None:
        self.a = pin_a
        self.b = pin_b
        self.c = pin_c
        self.d = pin_d
        self.cur_val = 0
        self.reg = 0
        self.delay_us = delay_us
    
    
    def set_delay(self, delay_us:int) -> None:
        self.delay_us = delay_us
        
    
    def _set(self, a: int, c: int, b: int, d: int) -> None:
        self.a(a)
        self.b(b)
        self.c(c)
        self.d(d)
        
        time.sleep_us(self.delay_us)
    
    
    @property
    def steps(self):
        return self.cur_val
    
    
    def _set_reg(self) -> None:
        if self.reg == 0:
            self._set(1, 0, 0, 0)
            
        elif self.reg == 1:
            self._set(1, 1, 0, 0)

        elif self.reg == 2:
            self._set(0, 1, 0, 0)

        elif self.reg == 3:
            self._set(0, 1, 1, 0)

        elif self.reg == 4:
            self._set(0, 0, 1, 0)

        elif self.reg == 5:
            self._set(0, 0, 1, 1)

        elif self.reg == 6:
            self._set(0, 0, 0, 1)

        elif self.reg == 7:
            self._set(1, 0, 0, 1)
        
        
    def half_fwd(self):
        self.reg += 1
        if self.reg > 7:
            self.reg = 0
            
        self._set_reg()
        
        self.cur_val += 1    
        
    def half_rev(self):            
        self.reg -= 1
        if self.reg < 0:
            self.reg = 7
            
        self._set_reg()
        
        self.cur_val -= 1
        
    def fwd(self):       
        self.reg += 2
        if self.reg > 7:
            self.reg -= 8
            
        self._set_reg()
        
        self.cur_val += 2
        
    def rev(self):       
        self.reg -= 2
        if self.reg < 0:
            self.reg += 8
            
        self._set_reg()
        
        self.cur_val -= 2
        
    

spi = SPI(1, baudrate=30000000, sck=Pin(SCLK_Pin), mosi=Pin(MOSI_Pin))
display = st7789.ST7789(
    spi, 
    240, 
    135, 
    rotation=0, 
    rotations=ORIENTATIONS, 
    cs=Pin(CS_Pin, Pin.OUT), 
    reset=Pin(RESET_Pin, Pin.OUT), 
    dc=Pin(DC_Pin, Pin.OUT), 
    backlight=Pin(BL_Pin, Pin.OUT),	
)


display.init()
display.on()

button1 = Pin(Button1_Pin, Pin.IN, Pin.PULL_UP)
button2 = Pin(Button2_Pin, Pin.IN, Pin.PULL_UP)


a = Pin(27, Pin.OUT, value=0)
b = Pin(26, Pin.OUT, value=0)
c = Pin(25, Pin.OUT, value=0)
d = Pin(33, Pin.OUT, value=0)


sm = Stepper(
    pin_a=a, 
    pin_b=b, 
    pin_c=c, 
    pin_d=d, 
    delay_us=2000
)


while 1:
    ctr = 0
    sm.set_delay(2000)
    if not button1():
        sm.half_fwd()
        display.text(font_big, str(sm.steps / 100.0)+"mm    ", 0, 0)
        time.sleep_ms(300)
        while not button1(): 
            sm.set_delay(max(0, (200 - ctr) * 100))
            ctr += 1
            
            sm.half_fwd()
            display.text(font_big, str(sm.steps / 100.0)+"mm    ", 0, 0)
        
    if not button2():
        sm.half_rev()
        display.text(font_big, str(sm.steps / 100.0)+"mm    ", 0, 0)
        time.sleep_ms(300)
        while not button2(): 
            sm.set_delay(max(0, (200 - ctr) * 100))
            ctr += 1
            
            sm.half_rev()       
            display.text(font_big, str(sm.steps / 100.0)+"mm    ", 0, 0)
                
    if button1() and button2():
        display.text(font_big, str(sm.steps / 100.0)+"mm    ", 0, 0)
    
    