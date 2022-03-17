from hx711 import HX711

from machine import Pin, SoftSPI, SPI
import st7789, random, utime
import vga1_8x16 as font_small
import vga1_16x32 as font_big

BL_Pin = 4     #backlight pin
SCLK_Pin = 18  #clock pin
MOSI_Pin = 19  #mosi pin
MISO_Pin = 2   #miso pin

RESET_Pin = 23 #reset pin
DC_Pin = 16    #data/command pin
CS_Pin = 5     #chip select pin

Button1_Pin = 35; #right button
Button2_Pin = 0;  #left button
HORIZONTAL = 5
VERTICAL=0
MODE=HORIZONTAL

ORIENTATIONS = [
    (st7789.RGB,                          128, 160, 0, 0),
    (st7789.MADCTL_MX | st7789.MADCTL_MV, 160, 128, 0, 0),
    (st7789.MADCTL_MY | st7789.MADCTL_MX, 128, 160, 0, 0),
    (st7789.MADCTL_MY | st7789.MADCTL_MV, 160, 128, 0, 0),
]

ORIENTATIONS = [(0x00, 135, 240, 52, 40), (0x60, 240, 135, 40, 53), (0xc0, 135, 240, 53, 40), (0xa0, 240, 135, 40, 52)]

spi = SPI(1, baudrate=30000000, sck=Pin(SCLK_Pin), mosi=Pin(MOSI_Pin))
display = st7789.ST7789(
    spi, 
    240, 
    135, 
    rotation=1, 
    rotations=ORIENTATIONS, 
    cs=Pin(CS_Pin, Pin.OUT), 
    reset=Pin(RESET_Pin, Pin.OUT), 
    dc=Pin(DC_Pin, Pin.OUT), 
    backlight=Pin(BL_Pin, Pin.OUT)
    )

class Flag:
    def __init__(self):
        self._val = False

    def toggle(self):
        self._val = not self._val

    def trigger(self):
        self._val = True

    def clear(self):
        self._val = False
    
    def __bool__(self):
        return bool(self._val)


def print_center(string: str) -> None:
    string="   " + str(string) + "   "
    slen = len(string)*16
    display.text(font_big, string, int((240/2)-(slen/2)), int((135/2)-8))

do_tare = Flag()
def tare(evt):
    do_tare.trigger()
    print("taring...")

display.init()

display.on()

DATA_PIN_NR = 12
CLK_PIN_NR  = 13

hx = HX711(d_out=DATA_PIN_NR, pd_sck=CLK_PIN_NR, channel=HX711.CHANNEL_A_128)

button1 = Pin(Button1_Pin, Pin.IN, Pin.PULL_UP)
button1.irq(trigger=Pin.IRQ_FALLING, handler=tare) #interrupt for right button (button 1)

n_samples = 10
tare_val = 0

while 1:
    meas=0
    ts = utime.ticks_us()
    for i in range(n_samples):
        while not hx.is_ready():
            pass
        meas += hx.read()
    cycle = utime.ticks_us() - ts
    cycle /= 10**6

    meas /= n_samples
    meas /= 100

    if do_tare:
        do_tare.clear()
        tare_val = meas

    # print(meas)
    # display.fill(st7789.BLACK)
    print(meas)
    try:
        freq = "@ "+str(int(n_samples/cycle))+"Hz"
        display.text(font_small, freq, 0, 135-16)
    except:
        pass
    print_center(int(meas-tare_val))
