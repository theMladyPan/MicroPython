#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from machine import Pin, freq, SPI, ADC, UART, reset
import esp, time
from micropython import opt_level

# display imports
from ttgo_config import ORIENTATIONS, bind_display, message, TTGO_Pins
from  st7789 import ST7789, FAST
import vga1_8x16 as font_small
import vga1_16x32 as font_big
from uio import StringIO


opt_level(0) # change to 3 after done

esp.osdebug(0)
freq(240_000_000)
print("Mem free:", gc.mem_free())


spi = SPI(1, baudrate=30_000_000, sck=Pin(TTGO_Pins.SCLK), mosi=Pin(TTGO_Pins.MOSI))
display = ST7789(
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

bind_display(display, font_small, font_big, 3)
display.init()
display.on()
display.jpg("rubint.jpg", 0, 0, FAST)

Lbtn = Pin(TTGO_Pins.Lbtn, Pin.IN, Pin.PULL_UP)
Rbtn = Pin(TTGO_Pins.Rbtn, Pin.IN, Pin.PULL_UP)
batpin = ADC(Pin(14), atten=ADC.ATTN_11DB)
bat_volt = batpin.read_uv()*2*4.04/1_000_000

time.sleep(.2)
display.fill(0)

uart1 = UART(1, baudrate=9600, timeout=5, timeout_char=5, tx=13, rx=12)

try:
    while Rbtn():
        # main code goes here
        while not uart1.any(): ...
        line = uart1.readline().decode("utf-8").rstrip("\r\n")
        
        if line.startswith("$GPGGA"):
            head, utc_time, latitude, ns, longitude, ew, GPS_quality, n_of_sattelites, horizontal_precision, antenna_altitude, alt_units, geoid_height, geoid_units, age_of_data, checksum = line.split(",")
            print(line.split(","))
            message("Lat:    " + latitude + ns,         y=0,    big=False, clear=True)
            message("Long:   " + longitude + ew,        y=1*18, big=False)
            message("Prec:   " + horizontal_precision,  y=2*18, big=False)
            message("Alt:    " + antenna_altitude,      y=3*18, big=False)
            message("Time:   " + utc_time,              y=4*18, big=False)
            message("N_sat:  " + n_of_sattelites,       y=5*18, big=False)
            message("Age:    " + age_of_data,           y=6*18, big=False)
        
        if line.startswith("$GPGLL") and False:
            head, lat, ns, long, ew, utc_time, status, faa = line.split(",")
            print(lat, ns, long, ew, utc_time, status)
            message("lat:    " + lat + ns,   y=0,    big=False, clear=True)
            message("long:   " + long + ew,  y=1*18, big=False)
            message("time:   " + utc_time,   y=2*18, big=False)
            message("status: " + status,     y=3*18, big=False)

    

except Exception as e:
    # bind_display(display, font_small, font_big, 0)
    # display.orientation(3)

    s=StringIO()
    sys.print_exception(e, s)
    sys.print_exception(e)
    s=s.getvalue()
    if len(s) > 12*15:
        message(
            text=str(s[:12*15]),
            big=False,
            clear=True
        )
        time.sleep(3)
        message(
            text=str(s[12*15:]),
            big=False,
            clear=True
        )
        time.sleep(10)

reset()
##display.on()
#display.rotation(3)
#display.jpg("rubint.jpg", 0, 0, st7789.FAST)
#message("Goodbye...", big=False, y=115, x=130)
#time.sleep(3)
#display.off()
#deepsleep()