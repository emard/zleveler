#!/usr/bin/python3

# virtual serial port to the printer
# socat  pty,link=/dev/ttyACM0,raw  tcp:192.168.1.60:23
# ls -al /dev/ttyACM0
# rwxrwxrwx 1 root root 10 Sij  6 22:32 /dev/ttyACM0 -> /dev/pts/6
# chown your_username:your_username /dev/pts/6

import re, math
import numpy
import scipy
import scipy.spatial
import scipy.interpolate
import matplotlib
import matplotlib.pyplot

import inspect
import sys
import requests

import getopt
import os.path

import serial
import time

# Fabrikator ][ mini
#zhigh_nl = 5.0 # travel to newline Y with this high
#zhigh = 1.0 # travel to next Y with this high
#zstart = 0.4
#zlow = -0.4
#zstep = -0.05
#repeat = 3 # repeat measurement N times, averaging

#delay_connect = 10.0 # wait for serial connection
#delay0 = 10.0 # s to initially setup
#delaynl = 4.0 # s newline delay
#zdelay1 = 0.7 # s initial delay for z to move to first point
#zdelay = 0.01 # s delay for small read endstop status

#xmin=0
#xmax=95.001
#xstep=5
#xoffset=1 # added to x

#ymax=95
#ymin=-0.001
#ystep=-5
#yoffset=2 # added to y

#zoffset=-0.20 # added to z

# PRUSA i3mk3
zhigh_nl = 10.0 # travel to newline Y with this high
zhigh = 10.0 # travel to next Y with this high
zstart = 0.5
zlow = -0.5
zstep = -0.05
repeat = 3 # repeat measurement N times, averaging

delay_connect = 10.0 # wait for serial connection
delay0 = 40.0 # s to initially setup
delaynl = 10.0 # s newline delay
zdelay1 = 1.0 # s delay for z to move to next point
zdelay = 2.0 # s delay for small read endstop status (cca 0.01) or G30 delay (cca 5.0)
serdelay = 0.2 # s serial delay to read response

xmin=-2.0
xmax=210.001
xstep=10
xoffset=22 # added to x

ymin=-8.0
ymax=210.001
ystep=10
yoffset=8 # added to y

zoffset=-1.00 # added to z

# Probe type:
# M119: mechanical switch connected to Z-endstop (fabrikator ][ mini)
# G30: firmware-supported probe (prusa i3mk3)
probe_type="G30"

def gcode_html(printer, cmd):
  r = requests.get("http://" + printer + "/set?code=" + cmd)
  return r.text

def gcode(printer, cmd, wait=serdelay):
  r = printer.write(cmd.encode('ascii')+b"\r")
  time.sleep(wait)
  response = printer.read(1)
  response += printer.read(printer.inWaiting())
  return response

printer_port="/dev/ttyACM0"
printer_fd=serial.Serial(printer_port, 115200, timeout=1)
print(printer_fd.name)
f = printer_fd

az  = {} # empty associative Z-level array
an  = {} # empty associative count array

output_filename="zlevel.xyz"
output_fd=open(os.path.expanduser(output_filename), "w")
zlevel = output_fd

if 1 == 1:
    print("connecting")
    time.sleep(delay_connect)
    print("start zprobe")
    # Fabrikator ][ mini
    #gcode(f,"G90; absolute positioning")
    #gcode(f,"M203 Z2; fast Z feedrate 2 mm/s (120 mm/s)")
    #gcode(f,"M140 S57; heat bed to 57'C")
    #gcode(f,"G28 X Y; go home XY but not Z")
    #gcode(f,"G0 X50 Y50; go to center of the bed")
    #gcode(f,"G28 Z; go home Z now at center of the bed")
    #gcode(f,"M119; read endstop status")
    # PRUSA i3mk3
    gcode(f,"G90; absolute positioning")
    gcode(f,"M140 S0") # heat bed off
    gcode(f,"M140 S85") # heat bed to 85'C
    gcode(f,"G28") # ; auto home with mesh leveling on PRUSA
    # common
    gcode(f,"G0 Z%.2f F5000" % zhigh_nl) # safety lift Z above
    time.sleep(delay0)

if ystep > 0:
  yfirst = ymin
  ylast = ymax
else:
  yfirst = ymax
  ylast = ymin

# with output_fd as zlevel:
n = 0
while n < repeat:
    x = xmin
    while x <= xmax:
      if ystep > 0:
        yfirst = ymin
        ylast = ymax
      else:
        yfirst = ymax
        ylast = ymin
      y = yfirst
      while (y - ylast) * ystep <= 0:
        # print("X%.2f Y%.2f " % (x,y))
        gcode(f, "G0 X%.2f Y%.2f" % (x,y))
        if y == yfirst:
          time.sleep(delaynl)
        if probe_type == "M119": # the measurement for mechanical switch
          z = zstart # set to start of probing point
          zswitch = 0
          while z > zlow and zswitch == 0:
            gcode(f, "G0 Z%.2f" % z)
            # print("Z%.2f" % z)
            if z == zstart:
              time.sleep(zdelay1)
            else:
              time.sleep(zdelay)
            endstop=gcode(f,"M119")
            # print(endstop)
            if b"z_stop: TRIGGERED" in endstop or b"z_min:H" in endstop:
              zswitch = 1
              # fill associative array
              aindex = "X%.2f Y%.2f" % (x+xoffset,y+yoffset)
              if aindex in an:
                az[aindex] += z+zoffset
                an[aindex] += 1
              else:
                az[aindex] = z+zoffset
                an[aindex] = 1
              print("%s Z%.2f # avg=%.2f n=%d" % (aindex,z+zoffset,az[aindex]/an[aindex],an[aindex]))
            z += zstep
        if probe_type == "G30": # measurement done by firmware (PRUSA i3MK3)
          endstop = gcode(f, "G30 X%.2f Y%.2f S-1" % (x,y), zdelay).decode("UTF-8")
          # endstop will among others report this line:
          # Bed X: 0.20000 Y: -3.80000 Z: 1.03167
          parse = re.match(r".*Bed X: (?P<X>[+-]?\d+[.]\d+) Y: (?P<Y>[+-]?\d+[.]\d+) Z: (?P<Z>[+-]?\d+[.]\d+).*", endstop, re.DOTALL)
          if parse: # re.match successful
            z = float(parse.group("Z"))
            aindex = "X%.2f Y%.2f" % (x+xoffset,y+yoffset)
            if aindex in an:
              az[aindex] += z+zoffset
              an[aindex] += 1
            else:
              az[aindex] = z+zoffset
              an[aindex] = 1
            print("%s Z%.2f # avg=%.2f n=%d" % (aindex,z+zoffset,az[aindex]/an[aindex],an[aindex]))
        y += ystep
        if y >= ymin:
          gcode(f, "G0 Z%.2f" % zhigh) # small lift in the same Y line
        else:
          gcode(f, "G0 Z%.2f" % zhigh_nl) # big lift, newline will follow
        time.sleep(zdelay1)
      x += xstep
      # after each completed Y-line, write Z-level file
      output_fd=open(os.path.expanduser(output_filename), "w")
      with output_fd as zlevel:
        for index in sorted(an):
          zlevel.write("%s Z%.2f\n" % (index,az[index]/an[index]))
        zlevel.close()
    n += 1

if 1 == 1: # leaving at center of hotbed
    gcode(f,"G0 X50 Y50; go to center of the bed")
    gcode(f,"M140 S0") # heat bed off
    gcode(f,"M140 S0") # heat bed off
    gcode(f,"G92;relative positioning")
    gcode(f,"M84;motors off")

print("zprobe completed. '%s' written." % output_filename)
