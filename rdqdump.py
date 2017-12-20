#!/usr/bin/python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com/jeff@jeffbryner.com
#
# Parser for rabbitmq .rdq files that attempts
# to find record delimeters, record length and
# output json of the record
# Assumes your rabbitmq events are json.
# example run: ./rdqdump.py -f 383506.rdq -c0 | less
#
#

import os
import sys
import io
from optparse import OptionParser
import json

def readChunk(data,start,end):
    data.seek(int(start))
    readdata=data.read(end)
    return readdata

#Hex dump code from:
# Author: Boris Mazic
# Date: 04.06.2012
#package rfid.libnfc.hexdump

def hexbytes(xs, group_size=1, byte_separator=' ', group_separator=' '):
    def ordc(c):
        return ord(c) if isinstance(c,str) else c

    if len(xs) <= group_size:
        s = byte_separator.join('%02X' % (ordc(x)) for x in xs)
    else:
        r = len(xs) % group_size
        s = group_separator.join(
            [byte_separator.join('%02X' % (ordc(x)) for x in group) for group in zip(*[iter(xs)]*group_size)]
        )
        if r > 0:
            s += group_separator + byte_separator.join(['%02X' % (ordc(x)) for x in xs[-r:]])
    return s.lower()



def hexprint(xs):
    def chrc(c):
        return c if isinstance(c,str) else chr(c)

    def ordc(c):
        return ord(c) if isinstance(c,str) else c

    def isprint(c):
        return ordc(c) in range(32,127) if isinstance(c,str) else c > 31

    return ''.join([chrc(x) if isprint(x) else '.' for x in xs])



def hexdump(xs, group_size=4, byte_separator=' ', group_separator='-', printable_separator='  ', address=0, address_format='%04X', line_size=16):
    if address is None:
        s = hexbytes(xs, group_size, byte_separator, group_separator)
        if printable_separator:
            s += printable_separator + hexprint(xs)
    else:
        r = len(xs) % line_size
        s = ''
        bytes_len = 0
        for offset in range(0, len(xs)-r, line_size):
            chunk = xs[offset:offset+line_size]
            bytes = hexbytes(chunk, group_size, byte_separator, group_separator)
            s += (address_format + ': %s%s\n') % (address + offset, bytes, printable_separator + hexprint(chunk) if printable_separator else '')
            bytes_len = len(bytes)

        if r > 0:
            offset = len(xs)-r
            chunk = xs[offset:offset+r]
            bytes = hexbytes(chunk, group_size, byte_separator, group_separator)
            bytes = bytes + ' '*(bytes_len - len(bytes))
            s += (address_format + ': %s%s\n') % (address + offset, bytes, printable_separator + hexprint(chunk) if printable_separator else '')

    return s

def convert_hex(string):
    return ''.join([hex(character)[2:].upper().zfill(2) \
                     for character in string])

if __name__ == '__main__':
    # search a rabbit mq rdq file for
    # potential amqp records:
    # by finding: 395f316c000000016d0000 , parsing the next 2 bytes as
    # record length and outputing the record to stdout
    #
    parser = OptionParser()
    parser.add_option("-b", dest='bytes'  , default=16, type="int", help="number of bytes to show per line")
    parser.add_option("-s", dest='start' , default=0, type="int", help="starting byte")
    parser.add_option("-l", dest='length' , default=16, type="int", help="length in bytes to dump")
    parser.add_option("-r", dest='chunk' , default=1024, type="int", help="length in bytes to read at a time")
    parser.add_option("-f", dest='input', default="",help="input: filename")
    parser.add_option("-t", dest='text', default="",help="text string to search for")
    parser.add_option("-o", dest='output', help="output: filename")

    # this hex value worked for me, might work for you
    # to delimit the entries in a rabbitmq .rdq file
    parser.add_option("-x", dest='hex', default="395f316c000000016d0000",help="hex string to search for")
    parser.add_option("-c", dest='count', default=1 ,type="int",help="count of hits to find before stopping (0 for don't stop)")
    parser.add_option("-d", "--debug",action="store_true", dest="debug", default=False, help="turn on debugging output")
    parser.add_option("-z", "--zero",action="store_true", dest="zero", default=False,help="when printing output, count from zero rather than position hit was found")

    (options,args) = parser.parse_args()


    if os.path.exists(options.input):
        src=open(options.input,'rb')
        #if the file is smaller than our chunksize, reset.
        options.chunk=min(os.path.getsize(options.input),options.chunk)
    else:
        sys.stderr.write(options.input)
        sys.stderr.write("No input file specified\n")
        sys.exit()

    if options.output is not None:
        output_file = options.output
        output = True
    else:
        output = False

    searchSize=max(len(options.text),len(options.hex)/2)
    data=readChunk(src,options.start,options.chunk)
    if options.debug:
        print("[*] position: %d"%(src.tell()))
    count=0
    while data:

        if len(options.hex)>0 and options.hex.upper() in convert_hex(data):
            #where is the string in this chunk of data
            hexdata=convert_hex(data)
            dataPos=hexdata.find(options.hex.upper())/2
            #where is the string in the file
            dataAddress=(max(0,(src.tell()-options.chunk))+dataPos)
            #what do we print in the hexoutput
            printAddress=dataAddress
            if options.zero:
                #used to carve out a portion of a stream and save it via xxd -r
                printAddress=0

            #set the length
            recordSize = readChunk(src, dataAddress + len(options.hex)/2,  2)
            rdqEntryLength = int(convert_hex(recordSize), 16)
            # print('rdqEntryLength:', rdqEntryLength)
            options.length = rdqEntryLength

            # backup, get the chunk of data requested starting at the search hit.
            # plus the hex search + the record length
            data=readChunk(src,dataAddress + len(options.hex)/2 + 2,options.length)
            unescapedData = data.decode('ascii', 'ignore')
            try:
                if output:
                    with open(output_file, "a") as out_file:
                        out_file.write(json.loads(unescapedData)+'\n')
                else:
                    sys.stdout.write(json.loads(unescapedData)+'\n')

            except Exception as e:
                if output:
                    with open(output_file, "a") as out_file:
                        out_file.write(unescapedData + '\n')
                else:
                    sys.stderr.write(unescapedData + '\n')
                pass
            if options.debug:
                print(hexdump(data, byte_separator='', group_size=2, group_separator=' ', printable_separator='  ', address=printAddress, line_size=16,address_format='%07X'))
            count+=1

        if options.count != 0 and options.count<=count:
            sys.exit()
        else:

            data=readChunk(src,src.tell(),options.chunk)
            if options.debug:
                print("[*] position: %d"%(src.tell()))
