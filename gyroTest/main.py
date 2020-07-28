import time
import mpu6050
import micropython
from machine import Pin
micropython.alloc_emergency_exception_buf(100)

def isr(pin):
    print("Interrupt!")

mpu = mpu6050.Mpu6050(5,4)
mpu.get_values()
#server = mpuserver.MPUServer(mpu)
#server.serve()
