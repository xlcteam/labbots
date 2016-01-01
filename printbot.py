#
# PrintBot: a Tox bot that 3D prints .gcode files it receives
# Based on the echo.py script by Wei-Ning Huang (AZ) <aitjcize@gmail.com>
#
# Copyright (C) 2013 - 2014 Wei-Ning Huang (AZ) <aitjcize@gmail.com>
# All Rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

from __future__ import print_function

import sys
from pytox import Tox, ToxAV

from time import sleep
from os.path import exists
from subprocess import call

SERVER = [
    "192.210.149.121",
    33445,
    "F404ABAA1C99A9D37D61AB54898F56793E1DEF8BD46B1038B9D822E8460FAB67"
]

DATA = 'printbot.data'

# printbot.py features
# - accept friend request
# - print sent .gcode files on a 3D printer
# - talk to the user about the process


class AV(ToxAV):
    def __init__(self, core):
        super(AV, self).__init__(core)
        self.core = self.get_tox()

    def on_call(self, friend_number, audio_enabled, video_enabled):
        print("Incoming %s call from %d:%s ..." % (
            "video" if video_enabled else "audio", friend_number,
            self.core.friend_get_name(friend_number)))
        bret = self.answer(friend_number, 48, 64)
        print("Answered, in call..." + str(bret))

    def on_call_state(self, friend_number, state):
        print('call state:fn=%d, state=%d' % (friend_number, state))

    def on_bit_rate_status(self,
                           friend_number,
                           audio_bit_rate,
                           video_bit_rate):
        print('bit rate status: fn=%d, abr=%d, vbr=%d' %
              (friend_number, audio_bit_rate, video_bit_rate))

    def on_audio_receive_frame(self,
                               friend_number,
                               pcm,
                               sample_count,
                               channels,
                               sampling_rate):
        # print('audio frame: %d, %d, %d, %d' %
        #      (friend_number, sample_count, channels, sampling_rate))
        # print('pcm len:%d, %s' % (len(pcm), str(type(pcm))))
        sys.stdout.write('.')
        sys.stdout.flush()
        bret = self.audio_send_frame(friend_number,
                                     pcm,
                                     sample_count,
                                     channels,
                                     sampling_rate)
        if bret is False:
            pass

    def on_video_receive_frame(self, friend_number, width, height, frame):
        # print('video frame: %d, %d, %d, ' % (friend_number, width, height))
        sys.stdout.write('*')
        sys.stdout.flush()
        bret = self.video_send_frame(friend_number, width, height, frame)
        if bret is False:
            print('video send frame error.')
            pass

    def witerate(self):
        self.iterate()


class ToxOptions():
    def __init__(self):
        self.ipv6_enabled = True
        self.udp_enabled = True
        self.proxy_type = 0  # 1=http, 2=socks
        self.proxy_host = ''
        self.proxy_port = 0
        self.start_port = 0
        self.end_port = 0
        self.tcp_port = 0
        self.savedata_type = 0  # 1=toxsave, 2=secretkey
        self.savedata_data = b''
        self.savedata_length = 0


def save_to_file(tox, fname):
    data = tox.get_savedata()
    with open(fname, 'wb') as f:
        f.write(data)


def load_from_file(fname):
    return open(fname, 'rb').read()


INTRO_MSG = 'Hey, I am PrintBot and if you send me a .gcode file I can ' \
            ' try to print it out on the 3D printer I am connected to!'

HELP_MSG = 'I do not know what do you mean by that but if you send me a ' \
        '.gcode file I can sure try to print it out on the 3D printer I ' \
        'am connected to!'


class PrintBot(Tox):
    def __init__(self, opts=None):
        if opts is not None:
            super(PrintBot, self).__init__(opts)

        self.self_set_name("PrintBot")
        print('ID: %s' % self.self_get_address())

        self.connect()
        self.av = AV(self)
        self.files = {}

    def on_file_recv(self, fid, filenumber, kind, size, filename):
        print (fid, filenumber, kind, size, filename)
        if size == 0:
            return

        self.files[(fid, filenumber)] = {
            'f': open(filename, 'w'),
            'filename': filename
        }

        self.file_control(fid, filenumber, Tox.FILE_CONTROL_RESUME)

    def on_file_recv_chunk(self, fid, filenumber, position, data):
        if data is None:
            self.files[(fid, filenumber)]['f'].close()
            filename = self.files[(fid, filenumber)]['filename']
            print("Finished transfer of '{}'!".format(filename))
            if not filename.endswith('.gcode'):
                msg = "Sorry, I only print from .gcode files"
                self.friend_send_message(fid, Tox.MESSAGE_TYPE_NORMAL, msg)
                return

            msg = "Thanks, I got {}, printing it right away!".format(filename)
            self.friend_send_message(fid, Tox.MESSAGE_TYPE_NORMAL, msg)

            call(['printcore', '/dev/ttyUSB0', filename])

            msg = "I am happy to report {} is printed!".format(filename)
            self.friend_send_message(fid, Tox.MESSAGE_TYPE_NORMAL, msg)
            return

        self.files[(fid, filenumber)]['f'].write(data)
        print (fid, filenumber, position)

    def connect(self):
        print('connecting...')
        self.bootstrap(SERVER[0], SERVER[1], SERVER[2])

    def loop(self):
        checked = False
        save_to_file(self, DATA)

        try:
            while True:
                status = self.self_get_connection_status()

                if not checked and status:
                    print('Connected to DHT.')
                    checked = True

                if checked and not status:
                    print('Disconnected from DHT.')
                    self.connect()
                    checked = False

                self.av.witerate()
                self.iterate()
                sleep(0.01)
        except KeyboardInterrupt:
            save_to_file(self, DATA)

    def on_friend_request(self, pk, message):
        print('Friend request from {}: '.format(pk, message))
        self.friend_add_norequest(pk)
        print('Accepted.')
        fid = self.friend_by_public_key(pk)
        self.friend_send_message(fid, Tox.MESSAGE_TYPE_NORMAL, INTRO_MSG)
        save_to_file(self, DATA)

    def on_friend_message(self, friendId, type, message):
        name = self.friend_get_name(friendId)
        print('{}: {}'.format(name, message))
        print('PrintBot: {}'.format(HELP_MSG))
        self.friend_send_message(friendId, Tox.MESSAGE_TYPE_NORMAL, HELP_MSG)


opts = None
opts = ToxOptions()
opts.udp_enabled = True
if len(sys.argv) == 2:
    DATA = sys.argv[1]
    if exists(DATA):
        # opts = ToxOptions()
        opts.savedata_data = load_from_file(DATA)
        opts.savedata_length = len(opts.savedata_data)
        opts.savedata_type = Tox.SAVEDATA_TYPE_TOX_SAVE

t = PrintBot(opts)
t.loop()
