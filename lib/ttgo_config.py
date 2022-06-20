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

    Button1 = 35 # right button
    Button2 = 0  # left button

    Lbtn = Button2
    Rbtn = Button1

    BAT = 14

HORIZONTAL = 5
VERTICAL=0

ORIENTATIONS = [
    (0x00, 135, 240, 52, 40), 
    (0x60, 240, 135, 40, 53),
    (0xc0, 135, 240, 53, 40), 
    (0xa0, 240, 135, 40, 52)
]

display = None
font_small, font_big = None, None
orientation = None


def bind_display(disp, small, big, orient):
    global display, font_small, font_big, orientation
    display = disp
    font_small = small
    font_big = big
    orientation = orient


def message(text="", x=0, y=0, big=True, clear=False, wrap=True):
    global display, font_big, font_small, orientation
    if display is None:
        raise Exception("Open display and bind it first")

    if clear:
        display.fill(0)
    if orientation == 0 or orientation == 2:
        if big:
            font = font_big
            cl = 7
            yo = 30
        else:
            font = font_small  
            cl = 15
            yo = 15
    else:
        if big:
            font = font_big
            cl = 15
            yo = 30
        else:
            font = font_small  
            cl = 30
            yo = 15
            
    if len(text) > cl and wrap:
        for i in range(len(text)/cl):
            display.text(font, text[i*cl : i * cl + cl], x, y)
            y += yo
            
    else:
        display.text(font, text, x, y)