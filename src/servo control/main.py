import time,machine
from machine import Pin

#best PWM value for servo controller is 512-800 with frequency=500hz

def main(): #main routine
    D1=machine.PWM(machine.Pin(5),freq=500)
    time.sleep(1)
    D1.duty(505)
    time.sleep(1)
    #adc = machine.ADC(0)
    #D0=Pin(0, Pin.IN, pull=Pin.PULL_UP)

    while 1:
        for i in range(580,630,1):
            print(i)
            D1.duty(i)
            time.sleep(0.02)
        for i in range(580,630,1):
            print(1210-i)
            D1.duty(1210-i)
            time.sleep(0.02)

main()
