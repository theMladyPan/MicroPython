#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from machine import Pin, freq, SPI, ADC, UART, reset
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

bind_display(display, font_small, font_big, 3)
display.init()
display.on()
display.jpg("rubint.jpg", 0, 0, st7789.FAST)

Lbtn = Pin(TTGO_Pins.Lbtn, Pin.IN, Pin.PULL_UP)
Rbtn = Pin(TTGO_Pins.Rbtn, Pin.IN, Pin.PULL_UP)
batpin = ADC(Pin(14), atten=ADC.ATTN_11DB)
bat_volt = batpin.read_uv()*2*4.04/1_000_000

time.sleep(.2)
display.fill(0)

uart1 = UART(1, baudrate=9600, timeout=200, timeout_char=5, tx=13, rx=12)
color = st7789.WHITE

while Rbtn():     
    # main code goes here
    while not uart1.any(): ...
    data = uart1.readline()
    try:
        line = data.decode("utf-8").rstrip("\r\n")
        print(line)

        if line.startswith("$GPGGA"):
            head, utc_time, latitude, ns, longitude, ew, GPS_quality, n_of_sattelites, horizontal_precision, antenna_altitude, alt_units, geoid_height, geoid_units, age_of_data, checksum = line.split(",")
            if float(horizontal_precision) > 10:
                color = st7789.RED
            elif float(horizontal_precision) > 2:
                color = st7789.YELLOW
            else:
                color = st7789.GREEN

            message(f"Lat:    {latitude} {ns}    ", y=0, big=False, color=color)
            message(f"Long:   {longitude} {ew}    ", y=1*18, big=False, color=color)
            message(f"Prec:   {horizontal_precision}    ", y=2*18, big=False, color=color)
            message(
                f"Alt:    {antenna_altitude}{alt_units}    ",
                y=3 * 18,
                big=False,
                color=color,
            )
            message(f"Time:   {utc_time}    ", y=4*18, big=False, color=color)
            message(f"N_sat:  {n_of_sattelites}    ", y=5*18, big=False, color=color)
        if line.startswith("$GPVTG"):
            _, _, _, _, _, _, _, kmph, _, _ = line.split(",")
            message(f"Speed:  {kmph}km/h    ", y=6*18, big=False, color=color)

    except UnicodeError:
        continue
    except ValueError as e:
        s=StringIO()
        sys.print_exception(e, s)
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

    if line.startswith("$GPGLL") and False:
        head, lat, ns, long, ew, utc_time, status, faa = line.split(",")
        print(lat, ns, long, ew, utc_time, status)
        message(f"lat:    {lat}{ns}", y=0, big=False, clear=True)
        message(f"long:   {long}{ew}", y=1*18, big=False)
        message(f"time:   {utc_time}", y=2*18, big=False)
        message(f"status: {status}", y=3*18, big=False)

reset()
##display.on()
#display.rotation(3)
#display.jpg("rubint.jpg", 0, 0, st7789.FAST)
#message("Goodbye...", big=False, y=115, x=130)
#time.sleep(3)
#display.off()
#deepsleep()