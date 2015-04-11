#!/usr/bin/python

import struct
import sys

data = open(sys.argv[1], "rb").read()

colors=16
psize = colors/8
lsize = 0x40*psize

def getprev(buff):
    if len(buff)<lsize:
        return 0
    else:
        return struct.unpack("<H",buff[len(buff)-lsize:len(buff)-lsize+psize])[0]
        
        

while len(data) > 0:
    bhash, bsize1, bsize2, comp_size, flags = struct.unpack("<Q2H2L", data[:0x14])
    print "%16x %x %x %x %x" % (bhash, bsize1, bsize2, comp_size, flags)
    data = data[0x14:]
    bitmap = data[:comp_size]
    data = data[0x2000:]
    bmp_header="BM"+struct.pack('<6L2H6L', 0, 0, 54, 40, bsize1, bsize2, 1, colors, 0, len(bitmap), 0, 0, 0, 0)

    if flags & 0x8 == 0:
        open("/tmp/%x.bmp"%bhash,"wb").write(bmp_header+bitmap)
        continue

    ### DEBUG
    #if bhash != 0x19738266b759e697:
    #    continue
    ### DEBUG

    #fbmp = open("out.bmp", "wb")
    #fbmp.write(bmp_header+bitmap)
    #fbmp.close()
    fg = 0xffff
    out = ""
    while len(bitmap) > 0:
        code = ord(bitmap[0])
        bitmap = bitmap[1:]
        if (code & 0xc0) != 0xc0:
            # 3bit structure
            scode = code >> 5
            if scode == 0:
                # BG_RUN
                if (code & 0x1f) == 0:
                    blen = ord(bitmap[0])+32
                    bitmap = bitmap[1:]
                    print "MEGA_BG_RUN, len = %x" % blen
                else:
                    blen = code & 0x1f
                    print "BG_RUN, len = %x" % blen
                for i in xrange(blen):
                    out += struct.pack("<H", getprev(out))
            elif scode == 1:
                # MEGA_FG_RUN
                if (code & 0x1f) == 0:
                    blen = ord(bitmap[0])+32
                    bitmap = bitmap[1:]
                    print "MEGA_FG_RUN, len = %x" % blen
                else:
                    blen = code & 0x1f
                    print "FG_RUN, len = %x" % blen
                for i in xrange(blen):
                    out += struct.pack("<H", getprev(out)^fg)
            elif scode == 2:
                # MEGA_FG_BG_IMAGE
                if (code & 0x1f) == 0:
                    blen = ord(bitmap[0])+1
                    bitmap = bitmap[1:]
                    print "MEGA_FG_BG_IMAGE, len = %x" % blen
                else:
                    blen = (code & 0x1f)*8
                    print "FG_BG_IMAGE, len = %x" % blen
                bitleft = 0
                for i in xrange(blen):
                    if bitleft == 0:
                        byte = ord(bitmap[0])
                        bitmap = bitmap[1:]
                        bitleft = 8
#                        print "BYTE %x"%byte
                    bitval = (byte >> (8-bitleft)) & 0x1
                    bitleft -= 1
                    if bitval == 1:
                        bval = getprev(out) ^ fg
#                        print "BIT %d %x^%x"%(bitval,bval,fg)
                    else:
                        bval = getprev(out)
#                        print "BIT %d %x"%(bitval,bval)
                    out += struct.pack("<H", bval)
            elif scode == 3:
                # COLOR_RUN
                if (code & 0x1f) == 0:
                    blen = ord(bitmap[0])+32
                    bitmap = bitmap[1:]
                    print "MEGA_COLOR_RUN, len = %x" % blen
                else:
                    blen = (code & 0x1f)
                    print "COLOR_RUN, len = %x" % blen
                (bval,) = struct.unpack("<H", bitmap[:2])
                bitmap = bitmap[2:]
                for i in xrange(blen):
                    out += struct.pack("<H", bval)
            elif scode == 4:
                # COLOR_IMAGE
                if (code & 0x1f) == 0:
                    blen = ord(bitmap[0])+32
                    bitmap = bitmap[1:]
                    print "MEGA_COLOR_IMAGE, len = %x" % blen
                else:
                    blen = (code & 0x1f)
                    print "COLOR_IMAGE, len = %x" % blen
                for i in xrange(blen*psize):
                    out += bitmap[0]
                    bitmap = bitmap[1:]
            elif scode == 5:
                # PACKED_COLOR_IMAGE
                print bitmap[:10].encode('hex')
                if (code & 0x1f) == 0:
                    blen = ord(bitmap[0])+32
                    bitmap = bitmap[1:]
                    print "MEGA_PACKED_CLR_IMAGE, len = %x" % blen
                else:
                    blen = (code & 0x1f)
                    print "PACKED_COLOR_IMAGE, len = %x" % blen
                print "Error"
                sys.exit(1)
            else:
                print "Error scodex %x" % code
                sys.exit(1)
        elif (code & 0xe0) != 0xe0:
            scode = code & 0xf0
            if scode == 0xc0:
                # SET_FG_MEGA_FG_RUN
                if (code & 0xf) == 0:
                    blen = ord(bitmap[0])+16
                    bitmap = bitmap[1:]
                    print "SET_FG_MEGA_FG_RUN, len = %x" % blen
                else:
                    blen = code & 0xf
                    print "SET_FG_FG_RUN, len = %x" % blen
                (fg,) = struct.unpack("<H", bitmap[:2])
                bitmap = bitmap[2:]
                for i in xrange(blen):
                    out += struct.pack("<H", getprev(out)^fg)
            elif scode == 0xd0:
                if (code & 0xf) == 0:
                    blen = ord(bitmap[0])+1
                    bitmap = bitmap[1:]
                    print "SET_FG_MEGA_FG_BG, len = %x" % blen
                else:
                    blen = (code & 0xf)*8
                    print "SET_FG_FG_BG, len = %x" % blen
                (fg,) = struct.unpack("<H", bitmap[:2])
                bitmap = bitmap[2:]
                bitleft = 0
                for i in xrange(blen):
                    if bitleft == 0:
                        byte = ord(bitmap[0])
                        bitmap = bitmap[1:]
                        bitleft = 8
                    bitval = (byte >> (8-bitleft)) & 0x1
                    bitleft -= 1
                    if bitval == 1:
                        bval = getprev(out) ^ fg
                    else:
                        bval = getprev(out)
                    out += struct.pack("<H", bval)
            else:
                print "Error scode %x" % code
                sys.exit(1)
        elif (code & 0xf0) == 0xe0:
            # DITHERED_RUN
            if code & 0xf == 0:
                blen = ord(bitmap[0]) + 16
                bitmap = bitmap[1:]
                print "MEGA_DITHERED_RUN, len %x" % blen
            else:
                blen = code & 0xf
                print "DITHERED_RUN, len %x" % blen
            (color1, color2) = struct.unpack("<2H", bitmap[:4])
            bitmap = bitmap[4:]
            while blen > 0:
                out += struct.pack("<2H", color1, color2)
                blen -= 1
        elif code == 0xf0:
            # MEGA_MEGA_BG_RUN
            (blen,) = struct.unpack("<H", bitmap[:2])
            bitmap = bitmap[2:]
            print "MEGA_MEGA_BG_RUN, len = %x" % blen
            for i in xrange(blen):
                out += struct.pack("<H", getprev(out))
        elif code == 0xf1:
            # MEGA_MEGA_FG_RUN
            (blen,) = struct.unpack("<H", bitmap[:2])
            bitmap = bitmap[2:]
            print "MEGA_MEGA_FG_RUN, len = %x" % blen
            for i in xrange(blen):
                out += struct.pack("<H", getprev(out)^fg)
        elif code == 0xf2:
            # MEGA_MEGA_FGBG
            (blen,) = struct.unpack("<H", bitmap[:2])
            bitmap = bitmap[2:]
            print "MEGA_MEGA_FGBG, len = %x" % blen
            bitleft = 0
            for i in xrange(blen):
                if bitleft == 0:
                    byte = ord(bitmap[0])
                    bitmap = bitmap[1:]
                    bitleft = 8
                bitval = (byte >> (8-bitleft)) & 0x1
                bitleft -= 1
                if bitval == 1:
                    bval = getprev(out) ^ fg
                else:
                    bval = getprev(out)
                out += struct.pack("<H", bval)
        elif code == 0xf3:
            # MEGA_MEGA_COLOR_RUN
            (blen,bval) = struct.unpack("<2H", bitmap[:4])
            bitmap = bitmap[4:]
            print "MEGA_MEGA_COLOR_RUN of %x, len = %x" % (bval, blen)
            for i in xrange(blen):
                out += struct.pack("<H", bval)
        elif code == 0xf4:
            # MEGA_MEGA_CLR_IMG
            (blen,) = struct.unpack("<H", bitmap[:2])
            bitmap = bitmap[2:]
            print "MEGA_MEGA_CLR_IMG, len = %x" % blen
            for i in xrange(blen*psize):
                out += bitmap[0]
                bitmap = bitmap[1:]
        elif code == 0xf6:
            # MEGA_MEGA_SET_FG_RUN
            (blen,fg) = struct.unpack("<2H", bitmap[:4])
            bitmap = bitmap[4:]
            print "MEGA_MEGA_SET_FG_RUN, len = %x" % blen
            for i in xrange(blen):
                out += struct.pack("<H", getprev(out)^fg)
        elif code == 0xf7:
            # MEGA_MEGA_SET_FGBG
            (blen,fg) = struct.unpack("<2H", bitmap[:4])
            bitmap = bitmap[4:]
            print "MEGA_MEGA_SET_FGBG, len = %x" % blen
            bitleft = 0
            for i in xrange(blen):
                if bitleft == 0:
                    byte = ord(bitmap[0])
                    bitmap = bitmap[1:]
                    bitleft = 8
                bitval = (byte >> (8-bitleft)) & 0x1
                bitleft -= 1
                if bitval == 1:
                    bval = getprev(out) ^ fg
                else:
                    bval = getprev(out)
                out += struct.pack("<H", bval)
        elif code == 0xfd:
            print "WHITE"
            out += "\xff\xff"
        elif code == 0xfe:
            print "BLACK"
            out += "\x00\x00"
        else:
            print "Error code %x" % code
            open("out.bin","wb").write(out)
            sys.exit(1)
    open("/tmp/%x.bmp"%bhash,"wb").write(bmp_header+out)
    print "SZ",hex(len(out))
    if len(out) != (bsize1 * bsize2 * psize):
        print "SZ ERROR"
#    sys.exit(1)
