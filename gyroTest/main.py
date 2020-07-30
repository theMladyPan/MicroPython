import time
import mpu6050
import micropython
from machine import Pin, freq
import time

# micropython.alloc_emergency_exception_buf(100)

freq(int(16e7)) #160MHz
mpu = mpu6050.Mpu6050(scl=5, sda=4) #D1=SCL, D2=SDA

input("\n########\nStart ?")

while True:
    n = int(input("nOfSamples: "))
    with open("data.csv", "w") as subor:
        v=[]
        t=[]
        print("Starting measurement ...")
        for i in range(n):
            v.append(mpu.get_acz())
            t.append(time.ticks_ms())
        print("Measuring ended!\nWriting to memory ...")
        for i in range(n):
            zapisane = subor.write("\n"+str(t[i])+";"+str(v[i]))