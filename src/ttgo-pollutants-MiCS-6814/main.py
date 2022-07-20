#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from machine import Pin, freq, PWM, SPI, ADC, lightsleep, deepsleep, Timer
import esp, time

# display imports
from ttgo_config import ORIENTATIONS, bind_display, message, TTGO_Pins
import st7789
import vga1_8x16 as font_small
import vga1_16x32 as font_big

class OvervoltageError(Exception): ...

class APSensor:
    def __init__(self, adc: ADC, *, Rl: float, Ro: float, tf=lambda x:x, v_in: float=3.3) -> None:
        try:
            tf(1)
            self._tf = tf
        except:
            raise ValueError("tf must be callable with one argument")
        self._adc = adc
        self._Rl = float(Rl)
        self._Ro = float(Ro)
        self._atten = ADC.ATTN_0DB
        self._adc.atten(self._atten)
        self._v_in = float(v_in)
    
    def tare(self):
        Vo = self.sample(1000)
        Rs = self.Vo_to_Rs(Vo)
        self._Ro = Rs
        return Rs
    
    def atten0(self):
        self._adc.atten(ADC.ATTN_0DB) 

    def atten2_5(self):
        self._adc.atten(ADC.ATTN_2_5DB)
        
    def atten6(self):
        self._adc.atten(ADC.ATTN_6DB)

    def atten11(self):
        self._adc.atten(ADC.ATTN_11DB)

    def set_best_atten(self) -> bool:
        self.atten0()
        val = self._adc.read()
        if val < 4095:
            return True
        
        self.atten2_5()
        val = self._adc.read()
        if val < 4095:
            return True

        self.atten6()
        val = self._adc.read()
        if val < 4095:
            return True

        self.atten11()
        val = self._adc.read()
        if val < 4095:
            return True

        return False
    
    def sample(self, n_samples: int):
        n_samples = int(n_samples)

        if self.set_best_atten():
           # adc within adc limits 
            Vo = 0

            for i in range(n_samples):
                Vo += self._adc.read_uv()
            
            Vo /= n_samples
            Vo /= 1e6
            
            return Vo
        
        raise OvervoltageError("Voltage too high")

    def Vo_to_Rs(self, Vo:float) -> float:
        Rs = self._Rl / (self._v_in * ((1/Vo) - (1/self._v_in)))
        return Rs

    def measure(self, n_samples: int) -> float:
        Vo = self.sample(n_samples)
        Rs = self.Vo_to_Rs(Vo)
        return self._tf(Rs/self._Ro)


esp.osdebug(0)
freq(240_000_000)
print("Mem free:", gc.mem_free())

PIN_N_CO  = 13
PIN_N_NOX = 15
PIN_N_VOC = 2

adc_co  = ADC(Pin(PIN_N_CO) , atten=ADC.ATTN_11DB)
adc_nox = ADC(Pin(PIN_N_NOX), atten=ADC.ATTN_11DB)
adc_voc = ADC(Pin(PIN_N_VOC), atten=ADC.ATTN_11DB)

try:
    with open("cal.csv", "r") as cal_f:
        cal_vals = cal_f.read().split(";")
        Roco, Ronox, Rovoc = map(float, cal_vals)
        
except:
    Roco = 4e5
    Ronox = 1e4
    Rovoc = 1e5

s_co = APSensor(adc_co, Rl=100_000, Ro = Roco, tf=lambda x: (4.17*x)**(-1.18))
# ppm = 0,162*x + -9,75E-03; where x=Rs/Ro
s_nox = APSensor(adc_nox, Rl=10_000, Ro = Ronox, tf=lambda x: (.162*x)-9.75e-3)
# ppm = 0,277x^-2,59; where x=Rs/Ro
s_voc = APSensor(adc_voc, Rl=100_000, Ro = Rovoc, tf=lambda x: (.277*x)**(-2.59))


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

bind_display(display, font_small, font_big, 0)
display.init()
display.on()
display.jpg("rubint.jpg", 0, 0, st7789.FAST)

Lbtn = Pin(TTGO_Pins.Lbtn, Pin.IN, Pin.PULL_UP)
Rbtn = Pin(TTGO_Pins.Rbtn, Pin.IN, Pin.PULL_UP)

batpin = ADC(Pin(14), atten=ADC.ATTN_11DB)

bat_volt = batpin.read_uv()*2*4.04/1_000_000

time.sleep(1)
# display.rotation(0)
display.fill(0)

def tare():
    Ro1 = s_co.tare()
    Ro2 = s_nox.tare()
    Ro3 = s_voc.tare()
    message("CO  Ro: {:d} Ohm    ".format(int(Ro1)), wrap=False, big=False,  y=0)
    message("NOX Ro: {:d} Ohm    ".format(int(Ro2)), wrap=False, big=False, y=20)
    message("VOC Ro: {:d} Ohm    ".format(int(Ro3)), wrap=False, big=False, y=40)
    with open("cal.csv", "w") as cal_f:
        cal_f.write("{};{};{}".format(Ro1, Ro2, Ro3))

while 1:
    display.fill(0)
    while not Lbtn():
        tare()

    display.fill(0)
    while Lbtn():
        bat_volt = bat_volt * .9 + batpin.read_uv()*2*4.04/10_000_000
        if bat_volt > 5:
            bat_volt = 5
        h, m, s = time.time()//3600, time.time()//60, int(time.time())
        message("BAT: {:0.2f}V, ON: {:02d}h{:02d}m{:02d}s".format(bat_volt, h, m, s), big=False, wrap=False)

        v_co = s_co.measure(1000)
        v_nox = s_nox.measure(1000)
        v_voc = s_voc.measure(1000)

        message("CO*: {:0.3f}ppm ".format(v_co) , y=20, big=True, wrap=False)
        message("NOx: {:0.3f}ppm ".format(v_nox), y=50, big=True, wrap=False)
        message("VOC: {:0.0f}ppm ".format(v_voc), y=80, big=True, wrap=False)
        message("* and other reducing gases", y=110, big=False, wrap=False)


display.on()
display.rotation(3)
display.jpg("rubint.jpg", 0, 0, st7789.FAST)
message("Goodbye...", big=False, y=115, x=130)
time.sleep(3)
display.off()
deepsleep()