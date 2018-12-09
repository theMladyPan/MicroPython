# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import gc
import webrepl
import machine
import settings
import network
webrepl.start()
gc.collect()

def reset_servo():
    pins=[5,4,0,2,14,12,13,15]
    for pin in pins:
        machine.PWM(machine.Pin(pin),freq=settings.pwm_freq, duty=settings.start_duty)

def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect('Kal-el', 'superman')
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())

reset_servo()
do_connect()
