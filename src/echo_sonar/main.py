# HC-SR04 Ultrasound Sensor
import time, machine
from machine import Pin


# WeMos D4 maps GPIO2 machine.Pin(2) = TRIGGER
# WeMos D2 maps GPIO4 machine.Pin(4) = ECHO

machine.freq(int(16e7)) 
triggerPort = 5
echoPort = 4

ptrig = Pin(triggerPort, Pin.OUT)
pecho = Pin(echoPort, Pin.IN)

input("Start?")

def trigger(us=10):
    ptrig.on()
    time.sleep_us(us)
    ptrig.off()

def measure():                                                                                                                                    
    trigger()                                                                                                                                  
    while not pecho.value(): pass     
    start = time.ticks_us()                                                                                                                       
    while pecho.value(): pass                                                                                                        
    end = time.ticks_us()   
    return time.ticks_diff(end, start)

# speed of sound = 340.29m/s
vs = 340.29
while True:
    raw_dist = measure()
    print(f"Distance: {str(raw_dist * vs / 2000)}mm", end="\r")
    time.sleep(0.1)
                                                                                                                                                