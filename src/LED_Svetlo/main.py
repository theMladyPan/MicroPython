from machine import Pin, PWM, TouchPad, lightsleep, freq
import time 

freq(20000000)

tp33 = TouchPad(Pin(33))
tp12 = TouchPad(Pin(12))
pwm0 = PWM(Pin(2), freq=10000, duty=0) # create and configure in one go
duty = 1

while 1:
    t33v = tp33.read()
    t12v = tp12.read()
    # print(duty)
    if t12v < 256:  # touched p12
        duty = int(duty/1.1)
        if duty < 1: 
            duty = 1
    elif t33v < 256:
        duty += 1
        duty = int(duty*1.1)
        if duty > 1023:
            duty = 1023
    pwm0.duty(duty)
    time.sleep_ms(50)