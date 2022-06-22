#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from machine import Pin, freq, SPI, ADC, reset, Timer
import esp, time
from micropython import opt_level

# display imports
from ttgo_config import ORIENTATIONS, bind_display, message, TTGO_Pins
import st7789 
import vga1_8x16 as font_small
import vga1_16x32 as font_big
from uio import StringIO


opt_level(0) # change to 3 after done

esp.osdebug(0)
freq(240_000_000)
print("Mem free:", gc.mem_free())


spi = SPI(1, baudrate=30_000_000, sck=Pin(TTGO_Pins.SCLK), mosi=Pin(TTGO_Pins.MOSI))
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
btn_tmr = Timer(0)

class Press(Timer):
    def __init__(self, _tnr: int, threshold_ms: int) -> None:
        super().__init__(int(_tnr))
        self.threshold = threshold_ms
        self._pressed = False
    
    def start(self, _evt=None):
        super().init()
    
    def stop(self, _evt=None):
        super().deinit()
        self._pressed = True
        
    @property
    def long(self):
        if super().value() >= self.threshold:
            return True
        return False

    @property
    def short(self):
        if super().value() > 0 and super().value() < self.threshold:
            return True
        return False
    
    @property
    def value(self):
        return super().value()
    
    def event(self, _evt:None):
        if _evt():
            self.stop()
        else:
            self.start()
            
    @property
    def pressed(self):
        pressed = self._pressed
        self._pressed = False
        return pressed
    
class Flipper(Pin):
    def __init__(self, pnr: int) -> None:
        super().__init__(pnr, Pin.OUT)    
        
    def flip(self, _evt: None) -> None:
        super().value(not super().value())
        

def duration_to_time(seconds: float):
    hours   = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)

    
def start_cycle(duration_hr: float): 
    display.fill(0)
    tmr1 = Timer(1)
    duration_ms = float(duration_hr) * 60 * 60 * 1000
    p=Pin(12, Pin.OUT, value=1)
    tmr1.init(period=int(duration_ms), mode=Timer.PERIODIC, callback=lambda _evt: p(not p()))
    while True:
        message("Output: {:4}".format("ON" if p() else "OFF"), color=st7789.GREEN if p() else st7789.RED)
        message(duration_to_time((duration_ms - tmr1.value())/1000)+"  ", y=30, )
        message(duration_to_time(tmr1.value()/1000)+"  ", y=60, color=(1<<14)+(1<<9)+(1<<3))
            
    
p1 = Press(0, threshold_ms=300)    
f12 = Flipper(12)

bind_display(display, font_small, font_big, 3)
display.init()
display.on()
display.jpg("rubint.jpg", 0, 0, st7789.FAST)

Lbtn = Pin(TTGO_Pins.Lbtn, Pin.IN, Pin.PULL_UP)
Rbtn = Pin(TTGO_Pins.Rbtn, Pin.IN, Pin.PULL_UP)

Lbtn.irq(trigger=Pin.IRQ_FALLING|Pin.IRQ_RISING, handler=p1.event)

batpin = ADC(Pin(14), atten=ADC.ATTN_11DB)
bat_volt = batpin.read_uv()*2*4.04/1_000_000

time.sleep(.3)
display.fill(0)

# menu:
# 1-2-6-24h cycle

durations = [0.1, 0.5, 1, 2, 4, 6, 12, 24]
pt = 0

while True:
    if pt >= len(durations):
        pt = 0
        
    message("Duration: {d}h  ".format(d=durations[pt]))
    message("Long press to start...", big=False, y=30)
    if p1.pressed:
        
        if p1.short:
            pt += 1
        elif p1.long:
            start_cycle(durations[pt])