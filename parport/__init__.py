# parport - Access the parallel port with python
# Copyright (C) 2007 Edgar Merino <donvodka at gmail dot com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
import libparport

BASE_PORT = 0x378
D0, D1, D2, D3, D4, D5, D6, D7 = \
        (1, 2, 4, 8, 16, 32, 64, 128)

def send(oneByte):
    libparport.writeOneByte(BASE_PORT, oneByte)

def read():
    return libparport.readOneByte(BASE_PORT)

class ParallelPort:
    "Interface to communicate with the Parallel Port"
    global BASE_PORT;

    def __init__(self, basePort= BASE_PORT):
        self.basePort = basePort #Puerto base, normalmente 0x378
    
    def read(self):
        return libparport.readOneByte(self.basePort)

    def write(self, oneByte):
        libparport.writeOneByte(self.basePort, oneByte)

