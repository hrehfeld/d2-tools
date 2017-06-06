#!/usr/bin/env python3
import struct

from struct import unpack_from, calcsize

import os

hog_filename = '/mnt/v/Games/descentVP/Descent 2/data/DESCENT2.HOG'

out_dir = 'out'

with open(hog_filename, 'rb') as f:
    data = f.read()

i = 3

h = data[:i].decode('ascii')
assert(h == 'DHF')

while i < len(data):
    f = '<13s'
    file_name = unpack_from(f, data, i)[0]
    i += calcsize(f)
    f = '<i'
    file_size = unpack_from(f, data, i)[0]
    i += calcsize(f)
    j = i + file_size
    file_data = data[i:j]
    i = j

    for j in range(len(file_name)):
        if file_name[j] == 0:
            break
    file_name = file_name[:j].decode('ascii')
    print(file_name, file_size)

    p = os.path.join(out_dir, file_name)
    with open(p, 'wb') as f:
        f.write(file_data)
    

#print(data)
