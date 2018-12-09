from settings import pwm_freq, start_duty
import machine

class RightRear:
    def __init__(self, x,y, position = 0):
        self.x=machine.PWM(machine.Pin(x),freq=pwm_freq, duty=start_duty)
        self.y=machine.PWM(machine.Pin(y),freq=pwm_freq, duty=start_duty)
        self.position = position

    def rotation(self, angle):
        self.x.duty(start_duty-angle)

    def stroke(self, angle):
        self.y.duty(start_duty-angle)

    def up(self):
        self.stroke(-200)
    def down(self):
        self.stroke(200)

    def fwd(self):
        self.rotation(200)
    def bck(self):
        self.rotation(-200)

    def update(self, position):
        position=position%500

        if position>450:
            self.up()
            self.rotation(((position-400)*8) - 200)
        else:
            self.down()
            self.rotation(400-position)

        self.position = position

class LeftRear(RightRear):
    def rotation(self, angle):
        self.x.duty(start_duty+angle)

    def stroke(self, angle):
        self.y.duty(start_duty+angle)

class LeftFront(RightRear):
    def rotation(self, angle):
        self.x.duty(start_duty+angle)

class RightFront(RightRear):
    def stroke(self, angle):
        self.y.duty(start_duty+angle)
