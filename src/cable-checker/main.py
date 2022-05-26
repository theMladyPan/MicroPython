#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from machine import Pin, freq, PWM, SPI, ADC, lightsleep, deepsleep, Timer
import esp, time

# display imports
from ttgo_config import ORIENTATIONS, bind_display, message, TTGO_Pins
import st7789
import vga1_8x16 as font_small
import vga1_16x32 as font_big

esp.osdebug(0)
freq(240_000_000)
print("Mem free:", gc.mem_free())


spi = SPI(1, baudrate=30_000_000, sck=Pin(TTGO_Pins.SCLK), mosi=Pin(TTGO_Pins.MOSI))
display = st7789.ST7789(
    spi, 
    240, 
    135, 
    rotation=0, 
    rotations=ORIENTATIONS, 
    cs=Pin(TTGO_Pins.CS, Pin.OUT), 
    reset=Pin(TTGO_Pins.RESET, Pin.OUT), 
    dc=Pin(TTGO_Pins.DC, Pin.OUT), 
    backlight=Pin(TTGO_Pins.BL, Pin.OUT),	
)

bind_display(display, font_small, font_big, 0)
display.init()
display.on()

Lbtn = Pin(TTGO_Pins.Lbtn, Pin.IN, Pin.PULL_UP)
Rbtn = Pin(TTGO_Pins.Rbtn, Pin.IN, Pin.PULL_UP)


class Sink:
    plus: Pin
    a: Pin
    b: Pin
    minus: Pin

    def __init__(self, plus: int, a: int, b: int, minus: int) -> None:
        self.plus   = Pin(plus, Pin.IN, Pin.PULL_DOWN) 
        self.a      = Pin(a, Pin.IN, Pin.PULL_DOWN)    
        self.b      = Pin(b, Pin.IN, Pin.PULL_DOWN)    
        self.minus  = Pin(minus, Pin.IN, Pin.PULL_DOWN)



class Source: 
    plus: Pin
    a: Pin
    b: Pin
    minus: Pin

    def __init__(self, plus: int, a: int, b: int, minus: int) -> None:
        self.plus   = Pin(plus, Pin.OUT) 
        self.a      = Pin(a, Pin.OUT)    
        self.b      = Pin(b, Pin.OUT)    
        self.minus  = Pin(minus, Pin.OUT)

        self.plus(0)
        self.a(0)
        self.b(0)
        self.minus(0)
        

source = Source(
    plus=12,
    a=13,
    b=15,
    minus=2
)

sink = Sink(
    plus=26,
    a=25,
    b=33,
    minus=32
)

batpin = ADC(Pin(14), atten=ADC.ATTN_11DB)

bat_volt = batpin.read_uv()*2*4.04/1_000_000


while 1:
    bat_volt = bat_volt * .9 + batpin.read_uv()*2*4.04/10_000_000
    if bat_volt > 5:
        message("Bat: 5V ", big=False, wrap=False)
    else:
        message("Bat: {:0.2f}".format(bat_volt)+"V  ", big=False, wrap=False)

    source.plus(1)
    if sink.plus():
        message("+ ---- +", y=174)
    else:
        message("+      +", y=174)
    source.plus(0)

    source.a(1)
    if sink.a():
        message("a ---- a", y=146)
    else:
        message("a      a", y=146)
    source.a(0)

    source.b(1)
    if sink.b():
        message("b ---- b", y=118)
    else:
        message("b      b", y=118)
    source.b(0)

    source.minus(1)
    if sink.minus():
        message("- ---- -", y=90)
    else:
        message("-      -", y=90)
    source.minus(0)
