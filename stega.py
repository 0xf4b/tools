#!/usr/bin/python
import sys

from PIL import Image
im = Image.open(sys.argv[1])

width, height = im.size

pix = im.load()

img = Image.new( 'RGB', (width*7,height))
pixels = img.load()

def tr(x):
    if x&1 == 0:
        return 0
    return 255

for y in xrange(height):
    for x in xrange(width):
        pixels[x,y] = (tr(pix[x,y][0]),tr(pix[x,y][1]),tr(pix[x,y][2]))
        pixels[x+width,y] = (tr(pix[x,y][0]),0,0)
        pixels[x+width*2,y] = (0,tr(pix[x,y][1]),0)
        pixels[x+width*3,y] = (0,0,tr(pix[x,y][2]))
        pixels[x+width*4,y] = (pix[x,y][0],0,0)
        pixels[x+width*5,y] = (0,pix[x,y][1],0)
        pixels[x+width*6,y] = (0,0,pix[x,y][2])
img.save("x.png")
