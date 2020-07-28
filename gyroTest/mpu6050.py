import machine


class Mpu6050:
    """
    This is a fork of:
    https://github.com/larsks/py-mpu6050

    See also other implementation:
    https://github.com/adamjezek98/MPU6050-ESP8266-MicroPython
    """
    def __init__(self, scl, sda):
        """
        Pins like machine.I2C
        """
        self.addr = 0x68
        self.i2c = machine.I2C(scl=machine.Pin(scl),
                               sda=machine.Pin(sda))

        self.i2c.start()
        self.i2c.writeto(self.addr, bytearray([107, 0]))
        self.i2c.stop()

    def get_raw_values(self):
        self.i2c.start()
        val = self.i2c.readfrom_mem(self.addr, 0x3B, 14)
        self.i2c.stop()
        return val

    def bytes_toint(self, firstbyte, secondbyte):
        if not firstbyte & 0x80:
            return firstbyte << 8 | secondbyte
        return - (((firstbyte ^ 255) << 8) | (secondbyte ^ 255) + 1)

    def get_values(self):
        raw_ints = self.get_raw_values()
        vals = {}
        vals["AcX"] = self.bytes_toint(raw_ints[0], raw_ints[1])
        vals["AcY"] = self.bytes_toint(raw_ints[2], raw_ints[3])
        vals["AcZ"] = self.bytes_toint(raw_ints[4], raw_ints[5])
        vals["Tmp"] = self.bytes_toint(raw_ints[6], raw_ints[7]) / 340.00 + 36.53
        vals["GyX"] = self.bytes_toint(raw_ints[8], raw_ints[9])
        vals["GyY"] = self.bytes_toint(raw_ints[10], raw_ints[11])
        vals["GyZ"] = self.bytes_toint(raw_ints[12], raw_ints[13])
        return vals  # returned in range of Int16
        # -32768 to 32767


    def enable_motion_detetection(self):
        SIGNAL_PATH_RESET = 0x68
        INT_PIN_CFG = 0x37
        ACCEL_CONFIG = 0x1C
        MOT_THR = 0x1F  # Motion detection threshold bits [7:0]
        MOT_DUR = 0x20  # Duration counter threshold for motion interrupt
                        # generation, 1 kHz rate, LSB = 1 ms
        MOT_DETECT_CTRL = 0x69
        INT_ENABLE = 0x38

        self.i2c.start()
        self.i2c.writeto(self.addr, bytearray([107, 0]))

        # Reset all internal signal paths in the MPU-6050 by writing 0x07 to
        # register 0x68
        self.i2c.writeto(self.addr, bytearray([SIGNAL_PATH_RESET, 0x07]))

        # write register 0x37 to select how to use the interrupt pin. For an
        # active high, push-pull signal that stays until register (decimal) 58
        # is read, write 0x20 or 0x60 for active low and push-pull.
        self.i2c.writeto(self.addr, bytearray([INT_PIN_CFG, 0x80]))

        # Write register 28 (==0x1C) to set the Digital High Pass Filter, bits
        # 3:0. For example set it to 0x01 for 5Hz. (These 3 bits are grey in
        # the data sheet, but they are used! Leaving them 0 means the filter
        # always outputs 0.)
        self.i2c.writeto(self.addr, bytearray([ACCEL_CONFIG, 0x01]))

        # write the desired Motion threshold to register 0x1F (For example,
        # write decimal 20).
        self.i2c.writeto(self.addr, bytearray([MOT_THR, 20]))

        # Set motion detect duration to 1  ms; LSB is 1 ms @ 1 kHz rate
        self.i2c.writeto(self.addr, bytearray([MOT_DUR, 40]))

        # to register 0x69, write the motion detection decrement and a few
        # other settings (for example write 0x15 to set both free-fall and
        # motion decrements to 1 and accelerometer start-up delay to 5ms total
        # by adding 1ms. )
        self.i2c.writeto(self.addr, bytearray([MOT_DETECT_CTRL, 0x15]))

        # write register 0x38, bit 6 (0x40), to enable motion detection interrupt.
        self.i2c.writeto(self.addr, bytearray([INT_ENABLE, 0x40]))
        self.i2c.stop()