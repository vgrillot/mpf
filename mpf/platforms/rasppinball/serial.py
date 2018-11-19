"""
RaspPinball communication management
"""

# !!181104:VG:Creation (refactoring, splitter main unit)


import logging
import asyncio
import time

from mpf.platforms.base_serial_communicator import BaseSerialCommunicator


class RaspSerialCommunicator(BaseSerialCommunicator):
    """Protocol implementation to the Arduino"""

    def __init__(self, platform, port, baud):
        """Initialise communicator. """
        self.frame_nb = 0
        self.received_msg = ''
        self.frames = {}
        super().__init__(platform, port, baud)

    def _parse_msg(self, msg):
        """Parse a message.

        Msg may be partial.
        Args:
            msg: Bytes of the message (part) received.
        """
        # !!181118:VG:Add some log info...
        try:
            self.received_msg += msg.decode()
            self.log.info('PARSING:%s' % str(msg))
        except Exception as e:
            self.log.warning("invalid concatframe, error='%s', msg='%s'" % (repr(e), msg))

        # !!181119:VG:Remove the while, manage only the first message
        try:
            pos = self.received_msg.find('\r')
            if pos == -1:  # no full msg
                break
            m = self.received_msg[:pos].strip()
            if not len(m):
                break
            self.received_msg = self.received_msg[pos + 1:]
            self.platform.process_received_message(m)
        except Exception as e:
            self.log.error("invalid parse frame, error='%s', msg='%s'" % (repr(e), m))
            raise  #!!!:to see the full strack trace

    @asyncio.coroutine
    def _identify_connection(self):
        """Initialise and identify connection."""
        #yield
        pass  # nothing to identify...
        # raise NotImplementedError("Implement!")

    def __send_frame(self, frame_nb, msg):
        """send a frame, store id and date it"""
        if frame_nb in self.frames:
            retry = self.frames[frame_nb]['retry'] + 1
        else:
            retry = 0
        if retry > 5:
            self.log.error('SEND:too many retry (%d) for frame "%s"' % (retry, msg))
            self.frames.pop(frame_nb)
            return
        self.frames[frame_nb] = {'msg': msg, 'time': time.time(), 'retry': retry}
        s = "!%d:%s\n" % (self.frame_nb, msg)
        self.log.info('SEND:%s' % s)
        self.send(s.encode())

    def __send_msg(self, msg):
        """send a new frame"""
        self.frame_nb += 1
        self.__send_frame(self.frame_nb, msg)

    def ack_frame(self, frame_nb, result):
        """an ack has been received, delete the according frame in buffer"""
        # !!170514:VG:Remove the frame only if ACK OK
        # !!181118:VG:Add log when frame acked
        if frame_nb in self.frames:
            if not result:
                self.log.error("ACK frame error '%s'" % self.frames[frame_nb])
            else:
                self.log.info("ACK frame done '%s'" % self.frames[frame_nb])
                self.frames.pop(frame_nb)

    def resent_frames(self):
        """resent all frame not acked after a timeout of 250ms"""
        try:
            for k, f in self.frames.items():
                if time.time() - f['time'] > 0.500:
                    self.log.warning("resend frame %d:%s" % (k, f['msg']))
                    self.__send_frame(k, f['msg'])
        except RuntimeError:
            pass  # dictionary changed size during iteration

    def rule_clear(self, coil_pin, enable_sw_id):
        msg = "RC:%s:%s" % (coil_pin, enable_sw_id)
        self.__send_msg(msg)

    def rule_add(self, hwrule_type, coil_pin, enable_sw_id='0', disable_sw_id='0', duration=10):
        msg = "RA:%d:%s:%s:%s:%d" % (hwrule_type, coil_pin, enable_sw_id, disable_sw_id, duration)
        self.__send_msg(msg)

    def driver_pulse(self, coil_pin, duration):
        # !!170418:VG:Add duration
        msg = "DP:%s:%d" % (coil_pin, duration)
        self.__send_msg(msg)

    def driver_enable(self, coil_pin):
        msg = "DE:%s" % (coil_pin)
        self.__send_msg(msg)

    def driver_disable(self, coil_pin):
        msg = "DD:%s" % (coil_pin)
        self.__send_msg(msg)

    def msg_init_platform(self):
        """message init platform, call when the platform try to init the communication
           with the slave board
        """
        msg = 'MI'
        self.__send_msg(msg)

    def msg_halt_platform(self):
        """message halt platform, call when the platform is goingn to quit"""
        msg = 'MH'
        self.__send_msg(msg)
