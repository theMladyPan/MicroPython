# from machine import RTC, ADC, Pin, SPI, UART, Timer
from hx711 import HX711

DATA_PIN_NR = 32
CLK_PIN_NR  = 33

hx = HX711(d_out=DATA_PIN_NR, pd_sck=CLK_PIN_NR, channel=HX711.CHANNEL_A_128)
while 1:
    if hx.is_ready():
        print(hx.read())