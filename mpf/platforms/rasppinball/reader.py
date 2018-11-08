#!/usr/bin/python3 -u

#
# This is just a very bad terminal to debug arduino communication
#


import time
import serial
import sys
import threading


ser = serial.Serial(
    port='/dev/ttyAMA0',
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1)

class Reader(threading.Thread):
    def __init__(self, serial_port):
        #super().__init__(self)
        threading.Thread.__init__(self)
        self.ser = ser
        self.stop = False

    def run(self):
        t = time.time()
        while not self.stop:
            r = ser.readline()
            if r:
                tt = time.time() - t
                t = time.time()
                print('%f %s' % (tt, r.decode().strip()))


reader = Reader(ser)
reader.start()
try:

    while True:
        cmd = input('-->')
        if cmd == 'q':
            break
        if cmd:
            cmd += '\n'
            ser.write(cmd.encode())
finally:
    reader.stop = True
reader.wait()
print("END.");
