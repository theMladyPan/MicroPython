#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import struct
import sys
from machine import Pin, freq, SPI, ADC, deepsleep, I2C, UART, reset
import esp, time
from micropython import opt_level

# display imports
from ttgo_config import ORIENTATIONS, bind_display, message, TTGO_Pins
from sen5x_lite import SEN5x
from  st7789 import ST7789, FAST
import vga1_8x16 as font_small
import vga1_16x32 as font_big
from xerxes_node import Node
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
    rotation=0, 
    rotations=ORIENTATIONS, 
    cs=Pin(TTGO_Pins.CS, Pin.OUT), 
    reset=Pin(TTGO_Pins.RESET, Pin.OUT), 
    dc=Pin(TTGO_Pins.DC, Pin.OUT), 
    backlight=Pin(TTGO_Pins.BL, Pin.OUT),	
)

bind_display(display, font_small, font_big, 3)
display.init()
display.on()
display.rotation(3)
display.jpg("rubint.jpg", 0, 0, FAST)

Lbtn = Pin(TTGO_Pins.Lbtn, Pin.IN, Pin.PULL_UP)
Rbtn = Pin(TTGO_Pins.Rbtn, Pin.IN, Pin.PULL_UP)
batpin = ADC(Pin(14), atten=ADC.ATTN_11DB)

i2c = I2C(1, scl=Pin(26, Pin.PULL_UP), sda=Pin(27, Pin.PULL_UP), freq=50_000)

sen = SEN5x(i2c)

if not Lbtn():
    message("Setup mode activated", big=False)
    sys.exit(0) 

bat_volt = batpin.read_uv()*2*4.04/1_000_000

sen.start()
time.sleep(1)
display.fill(0)
display.rotation(0)
bind_display(display, font_small, font_big, 0)

usb_uart = UART(1, baudrate=115_200, timeout=5, timeout_char=5, tx=1, rx=3)
# print("Measurement started")
# print('Product Name:', sen.product_name)
# print('Serial Number:', sen.serial_number)

raw_data = (0 for i in range(8))

def fetcher():
    global raw_data
    # pm1, pm2, pm4, pm10, rh, t, voc, nox = sen.measured_values_raw

    return struct.pack("!ffffffff", *raw_data)

xn = Node(
    com=usb_uart,
    address=0x20,
    device_id= 0x50,
    timeout=5
)
xn.bind_fetch_handler(handler=fetcher)

try:

    while Rbtn():
        # main code goes here

        while not sen.data_ready and not sen.status: 
            try:
                if xn.sync():
                    message('Synced!    ', y=18*10 , big=False)
            except TypeError:
                    message('Not synced!', y=18*10 , big=False)

        raw_data = sen.measured_values_raw
        pm1, pm2, pm4, pm10, rh, t, voc, nox = raw_data
        
        pm2 -= pm1
        pm4 -= pm2 + pm1
        pm10 -= pm4 + pm2 + pm1

        if not pm1 is None and not usb_uart.any(): 
            message('PM1:    ' + "{:3.1f}".format(pm1)                + 'ug/m3  ' , y=18*0 , big=False)
        if not pm2 is None and not usb_uart.any(): 
            message('PM2.5:  ' + "{:3.1f}".format(pm2)                + 'ug/m3  ' , y=18*1 , big=False)
        if not pm4 is None and not usb_uart.any(): 
            message('PM4:    ' + "{:3.1f}".format(pm4)                + 'ug/m3  ' , y=18*2 , big=False)
        if not pm10 is None and not usb_uart.any(): 
            message('PM10:   ' + "{:3.1f}".format(pm10)               + 'ug/m3  ' , y=18*3 , big=False)
        if not rh is None and not usb_uart.any(): 
            message('RH:     ' + "{:3.1f}".format(rh)                 + '%  '     , y=18*4 , big=False)
        if not t is None and not usb_uart.any(): 
            message('Temp:   ' + "{:3.1f}".format(t)                  + 'oC '     , y=18*5 , big=False)
        if not voc is None and not usb_uart.any(): 
            message('VOC:    ' + "{:3.1f}".format(voc)                + 'i  '     , y=18*6 , big=False)
        if not nox is None and not usb_uart.any(): 
            message('NOx:    ' + "{:3.1f}".format(nox)                + 'i  '     , y=18*7 , big=False)
        if not usb_uart.any():
            message('Status: ' + str(bin(sen.status))                 + '  '      , y=18*8 , big=False)
            message('             '                                               , y=18*10, big=False)
    

except Exception as e:
    # bind_display(display, font_small, font_big, 0)
    # display.orientation(3)

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

reset()
##display.on()
#display.rotation(3)
#display.jpg("rubint.jpg", 0, 0, st7789.FAST)
#message("Goodbye...", big=False, y=115, x=130)
#time.sleep(3)
#display.off()
#deepsleep()