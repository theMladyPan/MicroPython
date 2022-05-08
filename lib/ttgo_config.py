#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class TTGO_Pins:
    BL = 4     # backlight pin
    SCLK = 18  # clock pin
    MOSI = 19  # mosi pin
    MISO = 2   # miso pin

    RESET = 23 # reset pin
    DC = 16    # data/command pin
    CS = 5     # chip select pin

    Button1 = 35; # right button
    Button2 = 0;  # left button

HORIZONTAL = 5
VERTICAL=0

ORIENTATIONS = [
    (0x00, 135, 240, 52, 40), 
    (0x60, 240, 135, 40, 53),
    (0xc0, 135, 240, 53, 40), 
    (0xa0, 240, 135, 40, 52)
]