# -*- coding: utf-8 -*-

from machine import Pin, SPI, freq, ADC
from micropython import const
import utime as time
import math
from scl3300 import SCL3300, CS
from hx711 import HX711


freq(240_000_000)

from ttgo_config import TTGO_Pins, ORIENTATIONS, HORIZONTAL

# display imports
import st7789
import vga1_8x16 as font_small
import vga1_16x32 as font_big


# SCL3300 interface pins
SCLK_Pin    = 15   # clock pin
MOSI_Pin    = 13   # mosi pin
MISO_Pin    = 12   # miso pin
CS1_Pin     = 2    # chip select pin
CS2_Pin     = 17   # chip select pin

def stdev(data, xbar=None):
    if iter(data) is data:
        data = list(data)
    if xbar is None:
        xbar = sum(data)/len(data)
    total = total2 = 0
    for x in data:
        total += (x - xbar)**2
        total2 += (x - xbar) 
    total -= total2**2/len(data)
    return math.sqrt(total/(len(data) - 1))

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


class SampleRate:
    def __init__(self, val) -> None:
        self.val = val


incl1 = SCL3300(
    2, 
    baudrate=4_000_000, 
    sck=Pin(SCLK_Pin), 
    mosi=Pin(MOSI_Pin),
    miso=Pin(MISO_Pin), 
    cs=CS(CS1_Pin)
)

incl2 = SCL3300(
    2, 
    baudrate=4_000_000, 
    sck=Pin(SCLK_Pin), 
    mosi=Pin(MOSI_Pin),
    miso=Pin(MISO_Pin), 
    cs=CS(CS2_Pin)
)

incl1.init()
incl2.init()


hx1 = HX711(
    d_out=27, 
    pd_sck=26, 
    channel=HX711.CHANNEL_A_128
)


hx2 = HX711(
    d_out=25, 
    pd_sck=33, 
    channel=HX711.CHANNEL_A_128
)


spi = SPI(
    1, 
    baudrate=30_000_000, 
    sck=Pin(TTGO_Pins.SCLK), 
    mosi=Pin(TTGO_Pins.MOSI)
)

display = st7789.ST7789(
    spi, 
    240, 
    135, 
    rotation=3,  # 3 = horizontalne 
    rotations=ORIENTATIONS, 
    cs=Pin(TTGO_Pins.CS, Pin.OUT), 
    reset=Pin(TTGO_Pins.RESET, Pin.OUT), 
    dc=Pin(TTGO_Pins.DC, Pin.OUT), 
    backlight=Pin(TTGO_Pins.BL, Pin.OUT),	
)

display.init()
display.on()

f_show_std = Flag()
ns = SampleRate(10)

button1 = Pin(TTGO_Pins.Button1, Pin.IN, Pin.PULL_UP)
button2 = Pin(TTGO_Pins.Button2, Pin.IN, Pin.PULL_UP)

def adc_to_mm(val):
    return 22 * val / adc_span

adc_max = const(65300)
adc_min = const(2000)
adc_span = adc_max - adc_min

adc = ADC(Pin(32), atten=ADC.ATTN_11DB)  # read 150-2450mV

def show_stdev(evt):
    button1.irq(handler=None)
    f_show_std.toggle()
    time.sleep(.5)
    button1.irq(trigger=Pin.IRQ_FALLING, handler=show_stdev) #interrupt for right button (button 1)


def change_sample(evt):
    ns.val = 100 if ns.val == 10 else 10
    display.fill(0)
    display.text(font_big, "average of:", 0, 0)
    display.text(font_big, str(ns.val), 0, 40)
    display.text(font_big, "samples", 60, 40)
    time.sleep(1)
    display.fill(0)

button1.irq(trigger=Pin.IRQ_FALLING, handler=show_stdev) #interrupt for right button (button 1)
button2.irq(trigger=Pin.IRQ_FALLING, handler=change_sample) #interrupt for right button (button 1)


print("\n\n")
print("############################# Starting measurement #############################")
print("str1; std_s1; str2; std_s2; x1 [°]; std_x1; y1 [°]; std_y1; x2 [°]; std_x2; y2 [°]; std_y2; l1 [mm]; std_l1; time [ms]")

while 1:

    try:
        x, y = [], []
        for _ in range(ns.val):
            while not hx1.is_ready(): ...
            x.append(hx1.read())
            while not hx2.is_ready(): ...
            y.append(hx2.read())

        s1_avg = sum(x)/len(x)
        s2_avg = sum(y)/len(y)
        s1_std = stdev(x)
        s2_std = stdev(y)


        # measure first inclinometer
        x, y = [], []
        for _ in range(ns.val):
            xyz = incl1.read_ang()
            x.append(xyz.x)
            y.append(xyz.y)

        x1_avg = sum(x)/len(x)
        y1_avg = sum(y)/len(y)
        x1_std = stdev(x)
        y1_std = stdev(y)

        # measure second inclinometer
        x, y = [], []

        for _ in range(ns.val):
            xyz = incl2.read_ang()
            x.append(xyz.x)
            y.append(xyz.y)

        x2_avg = sum(x)/len(x)
        y2_avg = sum(y)/len(y)
        x2_std = stdev(x)
        y2_std = stdev(y)


        # measure sadc
        x = []

        for _ in range(ns.val):
            val16 = adc.read_u16()
            x.append(adc_to_mm(val16))

        l1_avg = sum(x)/len(x)
        l1_std = stdev(x)

        if f_show_std.is_set():
            display.text(font_small, f"sds1: {str(round(s1_std, 4))}     ", 0, 00)
            display.text(font_small, f"sds2: {str(round(s2_std, 4))}     ", 0, 18)
            display.text(font_small, f"sdx1: {str(round(x1_std, 4))}     ", 0, 36)
            display.text(font_small, f"sdy1: {str(round(y1_std, 4))}     ", 0, 54)
            display.text(font_small, f"sdx2: {str(round(x2_std, 4))}     ", 0, 72)
            display.text(font_small, f"sdy2: {str(round(y2_std, 4))}     ", 0, 90)
            display.text(font_small, f"sdl1: {str(round(l1_std, 4))}     ", 0, 108)
        else:
            display.text(font_small, f"s1  : {str(round(s1_avg, 4))}     ", 0, 00)
            display.text(font_small, f"s2  : {str(round(s2_avg, 4))}     ", 0, 18)
            display.text(font_small, f"x1  : {str(round(x1_avg, 4))}     ", 0, 36)
            display.text(font_small, f"y1  : {str(round(y1_avg, 4))}     ", 0, 54)
            display.text(font_small, f"x2  : {str(round(x2_avg, 4))}     ", 0, 72)
            display.text(font_small, f"y2  : {str(round(y2_avg, 4))}     ", 0, 90)
            display.text(font_small, f"l1  : {str(round(l1_avg, 4))}     ", 0, 108)


        print(
            s1_avg,
            s1_std,
            s2_avg,
            s2_std,
            x1_avg,
            x1_std,
            y1_avg,
            y1_std,
            x2_avg,
            x2_std,
            y2_avg,
            y2_std,
            l1_avg,
            l1_std,
            time.ticks_ms(),
            sep="; ",
        )

    except KeyboardInterrupt:
        raise

    except:
        pass  # just continue