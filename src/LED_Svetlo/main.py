from machine import Pin, PWM, freq, TouchPad
from time import sleep
import socket
import network
import _thread

LOW = "128"
HIGH = "512"

tp33 = TouchPad(Pin(33))
ap = network.WLAN(network.AP_IF) # create access-point interface
pwm0 = PWM(Pin(2), freq=1000, duty=0) # create and configure in one go

with open("duty.txt", "r") as ldf:
    last_duty = ldf.read()
with open("duty.txt", "w") as ldf:
    if last_duty == LOW:
        ldf.write(HIGH)
    else:
        ldf.write(LOW)
pwm0.duty(int(last_duty))

def loop():
    tpr = tp33.read()
    if tpr<200:
        last_s = ap.active()
        ap.active(not last_s)
        print("Wifi toggle")
    sleep(0.2)

t_parallel = _thread.start_new_thread(loop, ())

ap.config(essid='RA') # set the ESSID of the access point
ap.config(max_clients=10) # set how many clients can connect to the network
ap.active(True)         # activate the interface

def blink(pwm, n=4, t=0.1):
    duty = pwm.duty()
    for _ in range(1,n+1):
        pwm0.duty(1)
        sleep(t)
        pwm0.duty(0)
        sleep(t)
    pwm.duty(duty)

blink(pwm0, 3)

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print('listening on', addr)

while True:
    cl, addr = s.accept()
    # link(pwm0, 2)
    rcvd = cl.read()
    print('client connected from', addr, "received data:", rcvd)

    cl.close()
    try:
        duty = max(0, int(rcvd.rstrip(b"\n").decode()))
        pwm0.duty(duty)
        print("Duty set to %d"%duty)
    except ValueError:
        try:
            cmd = rcvd.rstrip(b"\n").decode()
            if "off" in cmd.lower():
                ap.active(False)
        except:
            pass
    except:
        pass
