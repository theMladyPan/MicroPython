import time,machine
from settings import pwm_freq, start_duty
from legs import LeftFront, LeftRear, RightFront, RightRear

#best PWM value for servo controller is 512-800 with frequency=500hz

def main(): #main routine
    pins=[5,4,0,2,14,12,13,15]
    lp, lz, pp, pz = LeftFront(0,2), LeftRear(14,12), RightFront(5,4), RightRear(13,15)
    legs = [lp, lz, pp, pz]
    pause = 0.04 #int(input("Pause [ms]"))/1000.0
    while 1:
        for i in range(0,500,20):
            for leg in range(len(legs)):
                legs[leg].update(i+leg*125)
            time.sleep(pause)

main()
