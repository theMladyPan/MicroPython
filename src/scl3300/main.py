# -*- coding: utf-8 -*-

import struct
from machine import Pin, SPI, freq
import utime as time
import math
from scl3300 import SCL3300, CS

freq(240_000_000)


SCLK_Pin    = 15  # clock pin
MOSI_Pin    = 2   # mosi pin
MISO_Pin    = 4   # miso pin
CS_Pin      = 5   # chip select pin


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


cspin = CS(CS_Pin)
incl = SCL3300(
    2, 
    baudrate=4_000_000, 
    sck=Pin(SCLK_Pin), 
    mosi=Pin(MOSI_Pin),
    miso=Pin(MISO_Pin), 
    cs=cspin
    )

incl.init()

ns = 210


while 1:
    ts = time.ticks_ms()
    x, y, z = [], [], []
    for i in range(ns):
        xyz = incl.read_ang()
        x.append(xyz.x)
        y.append(xyz.y)
        z.append(xyz.z)

    print(
        "avg(x): ", 
        sum(x)/len(x),
        "°, stdev(x):",
        stdev(x),
        "°, avg(y):", 
        sum(y)/len(y), 
        "°, stdev(y):",
        stdev(y),
        "°, avg(z):", 
        sum(z)/len(z), 
        "°, stdev(z):",
        stdev(z),
        "°, dt: ", 
        time.ticks_ms() - ts,
        "ms"
    )