# -*- coding: utf-8 -*-

from machine import Pin, SPI, freq
import utime as time
import math
from scl3300 import SCL3300, CS


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
    rotation=3, 
    rotations=ORIENTATIONS, 
    cs=Pin(TTGO_Pins.CS, Pin.OUT), 
    reset=Pin(TTGO_Pins.RESET, Pin.OUT), 
    dc=Pin(TTGO_Pins.DC, Pin.OUT), 
    backlight=Pin(TTGO_Pins.BL, Pin.OUT),	
)

display.init()
display.on()


button1 = Pin(TTGO_Pins.Button1, Pin.IN, Pin.PULL_UP)
button2 = Pin(TTGO_Pins.Button2, Pin.IN, Pin.PULL_UP)


show_stdev = False

ns = 80


while 1:

#     ts = time.ticks_ms()
    try:
        if not button1():
            show_stdev = False

        if not button2():
            show_stdev = True

        x, y = [], []
        for i in range(ns):
            xyz = incl1.read_ang()
            x.append(xyz.x)
            y.append(xyz.y)

        
        if show_stdev:
            display.text(font_big, "sdx1: " + str(round(stdev(x), 4)) + "     ", 0, 0)
            display.text(font_big, "sdy1: " + str(round(stdev(y), 4)) + "     ", 0, 34)
        else:
            display.text(font_big, "x1  : " + str(round(sum(x)/len(x), 4)) + "     ", 0, 0)
            display.text(font_big, "y1  : " + str(round(sum(y)/len(y), 4)) + "     ", 0, 34)

        x, y = [], []

        for i in range(ns):
            xyz = incl2.read_ang()
            x.append(xyz.x)
            y.append(xyz.y)

        if show_stdev:
            display.text(font_big, "sdx2: " + str(round(stdev(x), 4)) + "     ", 0, 68)
            display.text(font_big, "sdy2: " + str(round(stdev(y), 4)) + "     ", 0, 102)
        else:
            display.text(font_big, "x2  : " + str(round(sum(x)/len(x), 4)) + "     ", 0, 68)
            display.text(font_big, "y2  : " + str(round(sum(y)/len(y), 4)) + "     ", 0, 102)

    except:
        pass  # just continue

""" 
    print(
        "avg(x): ", 
        str(sum(x)/len(x)),
        "°, stdev(x):",
        str(stdev(x)),
        "°, avg(y):", 
        str(sum(y)/len(y)),
        "°, stdev(y):",
        str(stdev(y)),
        "°, avg(z):", 
        str(sum(z)/len(z)), 
        "°, stdev(z):",
        str(stdev(z)),
        "°, dt: ", 
        str(time.ticks_ms() - ts),
        "ms"
    ) """

