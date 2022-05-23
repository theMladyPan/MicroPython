#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random

import serial


def fetch(sercom: serial.Serial):
    data = sercom.readline()
    decoded = data.decode("utf-8")
    # print(decoded)

    return decoded.rstrip("\r\n").split(";")

def on_press(event):
    global subsetlen, fig
    if event.key == 'x':
        exit(0)
    elif event.key == "up":
        subsetlen = int(subsetlen * 1.2)
        print(f"Showing {subsetlen} results")

    elif event.key == "down":
        subsetlen = int(subsetlen / 1.2)
        print(f"Showing {subsetlen} results")

    else:
        print("Pressed:", event.key)

# Serial takes these two parameters: serial device and baudrate
ser = serial.Serial('/dev/ttyUSB0', 115200)
ser.write(b"\x03\x04")

rcvd = ""
while "# Starting measurement #" not in rcvd:
    rcvd = ser.readline().decode("utf-8")
    print(rcvd)

valnames = fetch(ser)[:-1]

t = []
vals = {}

for valname in valnames:
    vals[valname] = []

axes = []
lines = []

subsetlen = 20

plt.ion()

fig = plt.figure()

fig.canvas.mpl_connect('key_press_event', on_press)

for i in range (len(valnames)):
    axes.append(
        fig.add_subplot(4, 4, i+1)
    )
    lines.append(
        axes[i].plot([],[])[0]
    )
data_plot=plt.plot(0,0)

while 1:
    fresh = fetch(ser)
    try:
        t.append(float(fresh[-1]))

        i = 0
        for valname in valnames:
            vals[valname].append(float(fresh[i]))
            
            if len(t) > subsetlen:
                ysubset = vals[valname][-subsetlen:-1]
                xsubset = t[-subsetlen:-1]
            else:
                xsubset = t
                ysubset = vals[valname]

            lines[i].set_ydata(ysubset)
            lines[i].set_xdata(xsubset)
            
            axes[i].set_ylim(min(ysubset), max(ysubset)+.01) # +1 to avoid singular transformation warning
            axes[i].set_xlim(min(xsubset), max(xsubset)+.01)
            axes[i].set_title(valname)

            i += 1

        plt.draw()
        plt.pause(0.1)
    except ValueError: ...
    except KeyboardInterrupt: 
        raise

plt.show(block=True)
