#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import struct
from machine import Pin, freq, SPI, ADC, deepsleep, Timer, I2C, UART
import esp, time

# display imports
from ttgo_config import ORIENTATIONS, bind_display, message, TTGO_Pins
from sen5x_lite import SEN5x
import st7789
import vga1_8x16 as font_small
import vga1_16x32 as font_big
from xerxes_node import Node

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
display.rotation(3)
display.jpg("rubint.jpg", 0, 0, st7789.FAST)

Lbtn = Pin(TTGO_Pins.Lbtn, Pin.IN, Pin.PULL_UP)
Rbtn = Pin(TTGO_Pins.Rbtn, Pin.IN, Pin.PULL_UP)

batpin = ADC(Pin(14), atten=ADC.ATTN_11DB)

bat_volt = batpin.read_uv()*2*4.04/1_000_000

time.sleep(1)
display.rotation(0)
display.fill(0)

i2c = I2C(1, scl=Pin(26, Pin.PULL_UP), sda=Pin(27, Pin.PULL_UP), freq=50_000)


sen = SEN5x(i2c)

sen.start_measurement(0)
print("Measurement started")

print('Product Name:', sen.product_name)
print('Serial Number:', sen.serial_number)


def fetcher():
    # pm1, pm2, pm4, pm10, rh, t, voc, nox = sen.measured_values_raw
    return struct.pack("!ffffffff", sen.measured_values_raw)

xn = Node(
    com=UART(1, baudrate=115200, tx=22, rx=21, timeout=5, timeout_char=5),
    address=0x00,
    device_id= 0x50,
    timeout=5
)
xn.bind_fetch_handler(handler=fetcher)

while Rbtn():
    # main code goes here

    while not sen.data_ready: 
        xn.sync()
        
    pm1, pm2, pm4, pm10, rh, t, voc, nox = sen.measured_values_raw
    
    pm2 -= pm1
    pm4 -= pm2 + pm1
    pm10 -= pm4 + pm2 + pm1

    if not pm1 is None: 
        message('PM1:    ' + "{:3.1f}".format(pm1)                + 'ug/m3  ' , y=18*0 , big=False)
    if not pm2 is None: 
        message('PM2.5:  ' + "{:3.1f}".format(pm2)                + 'ug/m3  ' , y=18*1 , big=False)
    if not pm4 is None: 
        message('PM4:    ' + "{:3.1f}".format(pm4)                + 'ug/m3  ' , y=18*2 , big=False)
    if not pm10 is None: 
        message('PM10:   ' + "{:3.1f}".format(pm10)               + 'ug/m3  ' , y=18*3 , big=False)
    if not rh is None: 
        message('RH:     ' + "{:3.1f}".format(rh)                 + '%  '     , y=18*4 , big=False)
    if not t is None: 
        message('Temp:   ' + "{:3.1f}".format(t)                  + 'oC '     , y=18*5 , big=False)
    if not voc is None: 
        message('VOC:    ' + "{:3.1f}".format(voc)                + 'i  '     , y=18*6 , big=False)
    if not nox is None: 
        message('NOx:    ' + "{:3.1f}".format(nox)                + 'i  '     , y=18*7 , big=False)
    
    message('Status: ' + str(bin(sen.status))                 + '  '      , y=18*8 , big=False)


##display.on()
#display.rotation(3)
#display.jpg("rubint.jpg", 0, 0, st7789.FAST)
#message("Goodbye...", big=False, y=115, x=130)
#time.sleep(3)
display.off()
deepsleep()