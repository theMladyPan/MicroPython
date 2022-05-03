#!/usr/bin/env python3
# -*- coding: utf-8 -*-


BL_Pin = 4     # backlight pin
SCLK_Pin = 18  # clock pin
MOSI_Pin = 19  # mosi pin
MISO_Pin = 2   # miso pin

RESET_Pin = 23 # reset pin
DC_Pin = 16    # data/command pin
CS_Pin = 5     # chip select pin

Button1_Pin = 35; # right button
Button2_Pin = 0;  # left button
HORIZONTAL = 5
VERTICAL=0

ORIENTATIONS = [
    (0x00, 135, 240, 52, 40), 
    (0x60, 240, 135, 40, 53),
    (0xc0, 135, 240, 53, 40), 
    (0xa0, 240, 135, 40, 52)
]