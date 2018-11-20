import os
from subprocess import call
from time import time
from math import sqrt

from PIL import Image


def check(limit, ox, oy, px, py, current):
    lp = getpixel(px, py)
    if lp == -1:
        return current
    if lp != limit:
        nw = float(ox - px)
        nh = float(oy - py)
        new = (nw * nw) + (nh * nh)
        if new < current:
            current = new
    return current


def getField(limit, searchLen):
    print('Calculating field {0}...'.format(str(limit + 1)))
    if limit == 1:
        limit = 255
    distances = []
    for w in range(oim.size[0]):
        distances.append([])
        for h in range(oim.size[1]):
            current = limit if limit > 0 else (searchLen * searchLen)
            for x in range(w - searchLen, w + searchLen):
                for y in range(h - searchLen, h + searchLen):
                    current = check(limit, w, h, x, y, current)
            current = int(sqrt(current))
            current *= int(g)
            distances[w].append(current)
    return distances


def getpixel(x, y):
    try:
        p = inpixels[x, y][0]
        return p
    except IndexError:
        return -1


def generate():
    inPath = os.path.dirname(__file__)
    outPath = os.path.join(inPath, 'out.png')
    inPath = os.path.join(inPath, 'in.png')
    oim = Image.open(inPath).convert('RGBA')
    img = Image.new('RGBA', oim.size, (0, 0, 0, 0))

    ct = time()

    inpixels = oim.load()
    outpixels = img.load()

    search = 8
    last = 0.0
    g = 255 / search

    field1 = getField(0, search)
    ct = time() - ct
    print('Took: {0}'.format(str(round(ct, 1))))
    ct = time()
    field2 = getField(1, search)
    ct = time() - ct
    print('Took: {0}'.format(str(round(ct, 1))))
    ct = time()
    print('Mixing fields...')

    for cw in range(oim.size[0]):
        for ch in range(oim.size[1]):
            fc1 = 255 - field1[cw][ch]
            fc2 = field2[cw][ch]
            fc = int((fc1 + fc2)/2)
            outpixels[cw, ch] = (fc, fc, fc, 255)

    ct = time() - ct
    print('Took: {0}'.format(str(round(ct, 1))))
    ct = time()

    print('Resizing and saving output image (128 width)...')
    rf = float(oim.size[0]) / 128
    img = img.resize((128, int(oim.size[1] / rf)), Image.BILINEAR)

    img.save(outPath)

    ct = time() - ct
    print('Took: {0}'.format(str(round(ct, 1))))

