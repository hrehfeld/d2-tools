#!/usr/bin/env python3
import struct

from struct import unpack_from, calcsize

import os

from itertools import groupby, zip_longest
from pprint import pprint

in_filename = 'out/d2leva-3.rl2'

def parse(f, data, i):
    d = unpack_from(f, data, i)
    i += calcsize(f)
    return i, d
    

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def parse_vertices(data, i, max_len):
    f = '<BHH'
    d = unpack_from(f, data, i)
    version, num_vertices, num_cubes = d
    #print(i, version)
    i += calcsize(f)
    #always 0
    assert(version == 0)
    #print(num_vertices, num_cubes)
    #d2lvl3
    #assert(num_cubes == 336)
    #assert(num_vertices == 1228)

    vertices = []
    for j in range(num_vertices):
        p = []
        for k in range(3):
            # f = '<%sb' % str(4)
            # i, coords = parse(f, data, i)
            # #coords = grouper(coords, 4)
            # a, b, c, d = coords
            # c = a + 256 * b + (c + 256 * d)/ 65536
            f = '<i'
            i, c = parse(f, data, i)
            p.append(c[0] / 65536)
        vertices.append(p)
    
    def parse_cube(data, i):
        #neighbors
        f = '<B'
        neighbor_bitmask = unpack_from(f, data, i)[0]
        i += calcsize(f)

        ineighbors = [None] * 6
        for j in range(6):
            if (1 << j) & neighbor_bitmask:
                f = '<H'
                ineighbor = unpack_from(f, data, i)[0]
                i += calcsize(f)
                #0xfffe is the exit, 0xffff means no neighbor
                if ineighbor < 65535:
                    ineighbors[j] = ineighbor

        #cube vertices
        f = '<8h'
        ivertices = unpack_from(f, data, i)

        #print(len(cubes), ivertices)
        #if cubes:
            #pprint(cubes[-1])
        #print(parse('<64h', data, i)[1])
        for j, v in enumerate(ivertices):
            assert(v >= 0)
            assert(v < len(vertices))
        i += calcsize(f)

        #walls, doors
        f = '<B'
        special_wall_bitmask = unpack_from(f, data, i)[0]
        i += calcsize(f)

        ispecial_walls = [None] * 6
        for j in range(6):
            if (1 << j) & special_wall_bitmask:
                f = '<B'
                ispecial_wall= unpack_from(f, data, i)[0]
                i += calcsize(f)
                if ispecial_wall < 255:
                    ispecial_walls[j] = ispecial_wall

        #texcoords for normal walls
        texcoords = [None] * 6
        for j in range(6):
            if ineighbors[j] is None or ispecial_walls[j] is not None:
                i, itex = parse('<h', data, i)
                itex = itex[0]
                itex1 = None
                #(w->texture1 & 0x8000)
                assert(1 << 15  == 0x8000)
                if 1 << 15 & itex:
                    i, itex1 = parse('<h', data, i)
                    itex1 = itex1[0]
                    #FIXME
                    #w->txt2_direction = (w->texture2 >> 14)&3;
                    #w->texture2 &= 0x3fff;
                    itex1 &= 0x3fff;

                itex &= 0x3fff;

            
                uvls = []
                for k in range(4):
                    i, uvl = parse('<hhH', data, i)
                    uvls.append(uvl)

                texcoords[j] = (itex, uvls, itex1)
            

        return i, (ineighbors, ivertices, ispecial_walls, texcoords)

    cubes = []
    for j in range(num_cubes):
        i, c = parse_cube(data, i)
        cubes.append(c)

    assert(i <= max_len)
        
    f = '<' + 'BbBBI' * (num_cubes)
    i, cube_props = parse(f, data, i)
    cube_props = list(grouper(cube_props, 5))
    for p in cube_props:
        #FIXME
        assert(p[0] < 7)
        #(light >> 5)&0x7fff
        pass

    #print(i, max_len)
    #FIXME
    #assert(i == max_len)
    return i, vertices, cubes
        


with open(in_filename, 'rb') as f:
    data = f.read()

i, (h, version) = parse('<4si', data, 0)
assert(h == b'LVLP')
assert(6 <= version <= 8)


f = '<II11sIIII'
d = unpack_from(f, data, i)
#print(d)
imine_data, igame_data, palette, reactor_time, reactor_life, num_dyn_lights, secret_cube = d
assert(reactor_time == 0x1e)
assert(reactor_life == 0xffffffff)
i += calcsize(f)

i, secret_cube_orientation = parse('<9I', data, i)
#print(secret_cube_orientation)

#for some reason, initial header overlaps mine_data
#FIXME
#assert(i <= imine_data)
i, vertices, cubes = parse_vertices(data, imine_data, igame_data)

#obj export
print('mtllib foo.mtl')

for v in vertices:
    v = (v[0], -v[1], v[2])
    print('v %f %f %f' % tuple(v))

cube_faces = (
    (2, 3, 7, 6)
    , (0, 4, 7, 3)
    , (0, 1, 5, 4)
    , (1, 2, 6, 5)
    , (4, 5, 6, 7)
    , (0, 3, 2, 1)
)

cube_faces = [list(reversed(f)) for f in cube_faces]

for ic, c in enumerate(cubes):
    print('#cube %i' % ic)
    for i, nc in enumerate(c[0]):
        if nc is None:
            print('usemtl mtl%i' % i)
            vs = tuple(c[1][j] for j in cube_faces[i])
            print('f %i %i %i %i' % tuple(v+1 for v in vs))

