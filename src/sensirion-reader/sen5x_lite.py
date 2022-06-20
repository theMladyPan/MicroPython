from micropython import const
from time import sleep_ms
from struct import pack, unpack


def all_ones(b: bytes) -> bool:
    """
    Returns True if all bits are 1
    :param b: bytes
    :return: True if all 1's else False
    """
    n = int.from_bytes(b, 'big')
    return ((n + 1) & n == 0) and (n != 0)


class SEN5x:
    """
    Implements all capability on Sensirion SEN5x via I2C bus
    See README.md for details
    See example/main.py & test/main.py for usage

    Tested on:
        ESP32-C3-DevKitM-1
            https://docs.espressif.com/projects/esp-idf/en/v4.4.1/esp32c3/hw-reference/esp32c3/user-guide-devkitm-1.html
        Sensirion SEN54
            https://sensirion.com/products/catalog/SEN54
        MicroPython v1.18
            https://micropython.org/download/esp32c3

    Sources of information and inspiration:
        https://github.com/Sensirion/python-I2C-SEN5x
        https://github.com/agners/micropython-scd30/blob/master/scd30.py
    """
    class NotFoundError(Exception):
        """ SEN5x not found on I2C bus """
        pass

    class CRCError(Exception):
        """ Checksum error with SEN5x read/write per datasheet """
        pass

    class StatusError(Exception):
        """ Status error on SEN5x per datasheet"""
        pass

    class ReadError(Exception):
        """ I2C read error on SEN5x (observed, not clear in datasheet) """
        pass

    class InvalidMode(Exception):
        """ SEN5x in measurement mode when idle mode required or vice versa """
        pass

    # SEN5x I2C addresses
    DEFAULT_I2C_ADDR = const(0x69)
    START_MEASUREMENT = const(0x0021)
    START_MEASUREMENT_RHTGAS_ONLY = const(0x0037)
    STOP_MEASUREMENT = const(0x0104)
    DATA_READY_FLAG = const(0x0202)
    MEASURED_VALUES = const(0x03C4)
    START_FAN_CLEANING = const(0x5607)
    AUTO_CLEANING_INTERVAL = const(0x8004)
    PRODUCT_NAME = const(0xD014)
    SERIAL_NUMBER = const(0xD033)
    FIRMWARE_VERSION = const(0xD100)
    DEVICE_STATUS = const(0xD206)
    CLEAR_DEVICE_STATUS = const(0xD210)
    RESET_DEVICE = const(0xD304)

    # SEN5x Status masks
    FAN_SPEED_ERROR_MASK = const(1 << 21)
    FAN_CLEANING_ACTIVE_MASK = const(1 << 19)
    GAS_SENSOR_ERROR_MASK = const(1 << 7)
    RHT_ERROR_MASK = const(1 << 6)
    LASER_ERROR_MASK = const(1 << 5)
    FAN_FAIL_ERROR_MASK = const(1 << 4)

    I2C_BUFFER_SIZE = const(48)  # bytes, max used by product_line (must be divisible by 3)
    MIN_EXE_TIME = const(20)  # minimum time to execute I2C command in ms per datasheet

    # backup VOC_ALGORITHM_STATE
    CRC_TABLE = [  # see datasheet for checksum calculation
        0, 49, 98, 83, 196, 245, 166, 151, 185, 136, 219, 234, 125, 76, 31, 46,
        67, 114, 33, 16, 135, 182, 229, 212, 250, 203, 152, 169, 62, 15, 92, 109,
        134, 183, 228, 213, 66, 115, 32, 17, 63, 14, 93, 108, 251, 202, 153, 168,
        197, 244, 167, 150, 1, 48, 99, 82, 124, 77, 30, 47, 184, 137, 218, 235,
        61, 12, 95, 110, 249, 200, 155, 170, 132, 181, 230, 215, 64, 113, 34, 19,
        126, 79, 28, 45, 186, 139, 216, 233, 199, 246, 165, 148, 3, 50, 97, 80,
        187, 138, 217, 232, 127, 78, 29, 44, 2, 51, 96, 81, 198, 247, 164, 149,
        248, 201, 154, 171, 60, 13, 94, 111, 65, 112, 35, 18, 133, 180, 231, 214,
        122, 75, 24, 41, 190, 143, 220, 237, 195, 242, 161, 144, 7, 54, 101, 84,
        57, 8, 91, 106, 253, 204, 159, 174, 128, 177, 226, 211, 68, 117, 38, 23,
        252, 205, 158, 175, 56, 9, 90, 107, 69, 116, 39, 22, 129, 176, 227, 210,
        191, 142, 221, 236, 123, 74, 25, 40, 6, 55, 100, 85, 194, 243, 160, 145,
        71, 118, 37, 20, 131, 178, 225, 208, 254, 207, 156, 173, 58, 11, 88, 105,
        4, 53, 102, 87, 192, 241, 162, 147, 189, 140, 223, 238, 121, 72, 27, 42,
        193, 240, 163, 146, 5, 52, 103, 86, 120, 73, 26, 43, 188, 141, 222, 239,
        130, 179, 224, 209, 70, 119, 36, 21, 59, 10, 89, 104, 255, 206, 157, 172
    ]

    def __init__(self, i2c, address: int = DEFAULT_I2C_ADDR):
        self.i2c = i2c
        self.address = address
        # reuse buffers in effort to reduce heap fragmentation
        self._i2c_buffer = bytearray(self.I2C_BUFFER_SIZE)
        self._read_buffer = bytearray(self.I2C_BUFFER_SIZE * 2 // 3)  # no crc

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    @property
    def product_name(self) -> str:
        self._cmd_read(self.PRODUCT_NAME, num_words=16)
        return self._words_to_string(self._read_buffer)

    @property
    def serial_number(self) -> str:
        self._cmd_read(self.SERIAL_NUMBER, num_words=16)
        return self._words_to_string(self._read_buffer)

    @property
    def firmware_version(self) -> int:
        self._cmd_read(self.FIRMWARE_VERSION, num_words=1)
        return int(self._read_buffer[0])

    @property
    def data_ready(self) -> bool:
        """ Also used as a proxy for SEN5x idle|measurement mode """
        self._cmd_read(self.DATA_READY_FLAG, num_words=1)
        return bool(self._read_buffer[1])

    @property
    def measured_values_raw(self) -> tuple[float, float, float, float, float, float, float, float]:
        self._cmd_read(self.MEASURED_VALUES, num_words=8)
        ppm1_0, ppm2_5, ppm4_0, ppm10_0, rh, t, voc, nox = unpack('>4H4h', self._read_buffer)
        return (
            self._check_and_scale(ppm1_0, scale_factor=10),
            self._check_and_scale(ppm2_5, scale_factor=10),
            self._check_and_scale(ppm4_0, scale_factor=10),
            self._check_and_scale(ppm10_0, scale_factor=10),
            self._check_and_scale(rh, scale_factor=100),
            self._check_and_scale(t, scale_factor=200),
            self._check_and_scale(voc, scale_factor=10),
            self._check_and_scale(nox, scale_factor=10)
        )

    @property
    def auto_cleaning_interval(self) -> int:
        self._cmd_read(self.AUTO_CLEANING_INTERVAL, num_words=2)
        return unpack('>L', self._read_buffer)[0]

    @auto_cleaning_interval.setter
    def auto_cleaning_interval(self, interval) -> None:
        if not 0 <= interval <= 0xFFFFFFFF:
            raise ValueError('Interval out of range')
        self._cmd_write(self.AUTO_CLEANING_INTERVAL, pack('>L', interval))

    @property
    def status(self) -> int:
        self._cmd_read(self.DEVICE_STATUS, num_words=2)
        return unpack('>I', self._read_buffer)[0]

    @property
    def fan_cleaning_active(self) -> bool:
        return bool(self.status & self.FAN_CLEANING_ACTIVE_MASK)

    def start(self):
        """ use to start sensor measurement """
        self.check_i2c()
        self.reset()  # in case running
        self.start_measurement(0)
        self.check_for_errors()

    def stop(self):
        """ use to stop sensor measurement """
        self.stop_measurement()

    def start_measurement(self, num_checks: int = 100) -> bool:
        return self._start_measurement(self.START_MEASUREMENT, num_checks=num_checks)

    def start_measurement_rht_gas_only_mode(self, num_checks: int = 100) -> bool:
        return self._start_measurement(self.START_MEASUREMENT_RHTGAS_ONLY, num_checks=num_checks)

    def _start_measurement(self, cmd: int, num_checks: int = 100) -> bool:
        """ Starts measurement and waits until ready (num_checks = 0 to not wait) """
        self._cmd_exe(cmd, cmd_exe_time=50)
        for _ in range(num_checks):  # takes ~800 ms for data to be ready
            if self.data_ready:
                ready = True
                break
            else:
                sleep_ms(100)
        else:
            ready = False

        return ready

    def stop_measurement(self) -> None:
        self._cmd_exe(self.STOP_MEASUREMENT, cmd_exe_time=200)

    def start_fan_cleaning(self) -> None:
        if not self.data_ready:  # must be in measurement mode
            raise self.InvalidMode('Must be in measurement mode')
        self._cmd_exe(self.START_FAN_CLEANING)

    def check_i2c(self) -> None:
        try:
            if self.address not in self.i2c.scan():
                raise self.NotFoundError('I2C address not found')
        except Exception as e:
            raise self.NotFoundError(e)

    def check_for_errors(self) -> None:
        status = self.status
        if status & self.FAN_SPEED_ERROR_MASK:
            raise self.StatusError('Fan Speed Error')
        if status & self.GAS_SENSOR_ERROR_MASK:
            raise self.StatusError('Gas Sensor Error')
        if status & self.RHT_ERROR_MASK:
            raise self.StatusError('RHT Error')
        if status & self.LASER_ERROR_MASK:
            raise self.StatusError('Laser Error')
        if status & self.FAN_FAIL_ERROR_MASK:
            raise self.StatusError('Fan Fail Error')

    def clear_status(self) -> None:
        self._cmd_exe(self.CLEAR_DEVICE_STATUS)

    def reset(self) -> None:
        self._cmd_exe(self.RESET_DEVICE, cmd_exe_time=100)

    def _cmd_exe(self,
                 cmd: int,
                 cmd_exe_time: int = MIN_EXE_TIME,
                 ) -> None:
        """
        Executes I2C command to SEN5x with no response or data
        """
        self.i2c.writeto(self.address, pack('>H', cmd))
        sleep_ms(cmd_exe_time)  # time to execute before reading

    def _cmd_read(self,
                  cmd: int,
                  num_words: int,
                  cmd_exe_time: int = MIN_EXE_TIME,
                  ) -> None:
        """
        Executes I2C command and populates self._read_buffer with response from SEN5x
        Reads <num_words> words from SEN5x
        Each word is 2 bytes of data plus a checksum byte
        Validates and discards checksum
        """
        self._cmd_exe(cmd, cmd_exe_time=cmd_exe_time)
        self.i2c.readfrom_into(self.address, self._i2c_buffer)
        if all_ones(self._i2c_buffer):  # seems to return 0xFF words if data not available
            raise self.ReadError('Response not available')

        for i in range(num_words):
            msb = self._i2c_buffer[i * 3]
            lsb = self._i2c_buffer[i * 3 + 1]
            crc = self._i2c_buffer[i * 3 + 2]
            self._validate_crc(msb, lsb, crc)
            self._read_buffer[i * 2] = msb
            self._read_buffer[i * 2 + 1] = lsb

    def _cmd_write(self,
                   cmd: int,
                   words: bytes,  # can't be 0 or odd len()
                   cmd_exe_time: int = MIN_EXE_TIME
                   ) -> None:
        """
        Executes I2C command and writes data to SEN5x
        Each word is 2 bytes of data
        Generates checksum and writes data & checksum
        """
        for i in range(len(words) // 2):  # 2 bytes per word
            msb = words[i * 2]
            lsb = words[i * 2 + 1]
            crc = self._lookup_crc(msb, lsb)
            self._i2c_buffer[i * 3] = msb
            self._i2c_buffer[i * 3 + 1] = lsb
            self._i2c_buffer[i * 3 + 2] = crc
        # noinspection PyUnboundLocalVariable
        self.i2c.writeto_mem(self.address, cmd, self._i2c_buffer[:(i + 1) * 3], addrsize=16)
        sleep_ms(cmd_exe_time)

    @staticmethod
    def _validate_crc(msb: int, lsb: int, crc: int) -> None:
        if SEN5x._lookup_crc(msb, lsb) != crc:
            raise SEN5x.CRCError('Checksum error')

    @staticmethod
    def _lookup_crc(msb: int, lsb: int) -> int:
        """
        Returns SEN5x checksum based on 2 sequential bytes
        See datasheet for details
        """
        crc = 0xFF ^ msb
        crc = SEN5x.CRC_TABLE[crc] ^ lsb
        crc = SEN5x.CRC_TABLE[crc]

        return crc

    @staticmethod
    def _words_to_string(words: bytearray) -> str:
        for i in range(len(words)):  # bytearray doesn't support find()
            if words[i] == 0:  # found end
                break
        else:  # didn't find end
            raise ValueError('No terminator')
        return words[:i].decode('ascii')

    @staticmethod
    def _check_and_scale(int16: int, scale_factor: int = 1) -> [float, None]:
        """
        Measured Values scaling and check for 'unknown' value
        Datasheet indicates 0xFFFF is 'unknown'
        Sensirion drivers use 0x7FFF for 'unknown', which was seen in testing
        Returns None if 'unknown'
        """
        return int16 / scale_factor if int16 not in (0x7FFF, 0xFFFF) else None
