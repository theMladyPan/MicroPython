import time,machine
from machine import Pin

#best PWM value for servo controller is 512-800 with frequency=500hz

#5k POT on pin GND - A0 - +3V
#servo on pin D0

def main(): #main routine
    D1=machine.PWM(machine.Pin(5),freq=500)
    time.sleep(1)
    D1.duty(505)
    time.sleep(1)
    adc = machine.ADC(0)

    while 1:
            D1.duty(500+int(adc.read()/2))
            time.sleep(0.02)

main()