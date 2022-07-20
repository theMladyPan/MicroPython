import time
import gc
import random
import machine

from machine import Pin, ADC, Timer, WDT, freq, PWM
freq(50_000_000)

p25 = Pin(25, Pin.OUT)
p25(1)

time.sleep(3)
p25(0)

machine.lightsleep(5000)

def toggle(evt):    
    p25(not p25())

tim = Timer()


while True:
    freq(20_000_000)
    print("20MHz")
    time.sleep(3)

    freq(240_000_000)
    print("240MHz")
    time.sleep(3)
    print("lightsleep")
    time.sleep(1)
    machine.lightsleep(3000)
    p25(1)
    print("deepsleep")
    time.sleep(1)
    p25(0)
    machine.deepsleep(3000)

    
    
# machine.freq(48_000_000)

print("Mem free: ", gc.mem_free()//1024, "kB")

a26, a27, a28, a29 = [ADC(Pin(i, Pin.IN, Pin.PULL_DOWN)) for i in range(26, 30)]
pwm0 = PWM(p25)      # create PWM object from a pin
pwm0.freq(10000)         # set frequency
pwm0.duty_u16()         # get current duty cycle, range 0-65535

SMAX = 2**16 -1
SMIN = 10000

VMAX = 30
VMIN = -30

AMAX = 5
AMIN = -5

s = v = a = 0

while 1:
    a += (random.random() - .5)
    if a < AMIN: a = AMIN
    if a > AMAX: a = AMAX

    v += a
    if v < VMIN: v = VMIN
    if v > VMAX: v = VMAX

    s += v
    if s < SMIN: s = SMIN
    if s > SMAX: s = SMAX

    pwm0.duty_u16(int(s))
    # print(s, v, a)
    # time.sleep_ms(1)

while 1:
    p25(not p25())
    print([adc.read_u16() for adc in [a26, a27, a28, a29]])
    time.sleep_ms(1000)