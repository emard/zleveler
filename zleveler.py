#!/usr/bin/python3
#Name: ZLeveler
#Info: Postprocess adjustment of Z-level for CuraEngine g-code
#Depend: GCode
#Type: postprocess
#Param: zoffset(float:0.0) Global z-adjustment (mm)
#Param: tolayer(int:6) Adjust first n (layer nr)
#Param: xymax(float:10.0) Max xy travel, larger move splits (mm)
#Param: inputfile(string:"input.gcode") input g-code file
#Param: zlevelfile(string:"~/.zlevel.xyz") zlevel xyz matrix
#Param: outputfile(string:"output.gcode") output g-code file
#Param: view(int:0) View of zlevelfile

# Author: EMARD
# License: GPL
# https://github.com/emard/zleveler

import re, math
import numpy
import scipy
import scipy.spatial
import scipy.interpolate
import matplotlib
import matplotlib.pyplot

import inspect
import sys
import getopt
import os.path

zScale = 1
startEffect = 0

def plugin_standalone_usage(myName):
 print("Usage:")
 print("  "+myName+" -n layers_to_adjust -v 1 -z constant_offset -x max_xy_until_split -f input_gcode_file -l zlevel_file -o output_gcode_file")
 sys.exit()

try:
 inputfile
except NameError:
 # Then we are called from the command line (not from cura)
 opts, extraparams = getopt.getopt(
   sys.argv[1:],
   'n:v:z:u:t:x:i:l:o',
   ['toz=','view=','zoffset=','updown=','updown_threshold=','xymax=','inputfile=','levelfile=','outputfile=']
 )

 toLayer = 6;
 toZ = 1.0; # correct first 1 mm

 inputfile="-"
 zlevelfile="~/.zlevel.xyz"
 outputfile="-"
 view=0
 zoffset=0.0
 updown_threshold=0.0 # start experimenting with -0.03
 updown=0.0 # start experimenting with -0.07
 xymax=10.0

 for o,p in opts:
  if o in ['-n','--toz']:
   toZ = float(p)
  elif o in ['-v','--view']:
   view = int(p)
  elif o in ['-z','--zoffset']:
   zoffset = float(p)
  elif o in ['-u','--updown']:
   updown = float(p)
  elif o in ['-t','--updown_threshold']:
   updown_threshold = float(p)
  elif o in ['-x','--xymax']:
   xymax = float(p)
  elif o in ['-i','--inputfile']:
   inputfile = p
  elif o in ['-l','--levelfile']:
   zlevelfile = p
  elif o in ['-o','--outputfile']:
   outputfile = p
 if not inputfile:
  plugin_standalone_usage(inspect.stack()[0][1])

def getValue(line, key, default = None):
       if not key in line or (';' in line and line.find(key) > line.find(';')):
               return default
       subPart = line[line.find(key) + 1:]
       m = re.search('^[-]?[0-9]+\.?[0-9]*', subPart)
       if m == None:
               return default
       try:
               return float(m.group(0))
       except:
               return default

if inputfile == "-":
  input_fd = sys.stdin
else:
  input_fd = open(os.path.expanduser(inputfile), "r")

with input_fd as f:
  lines = f.readlines()

with open(os.path.expanduser(zlevelfile), "r") as f:
       xyzlines = f.readlines()

xyzlevel = []
for xyzline in xyzlines:
       x = getValue(xyzline, 'X', None)
       y = getValue(xyzline, 'Y', None)
       z = getValue(xyzline, 'Z', None)
       if x != None and y != None and z != None:
         xyzlevel.append({'X': x, 'Y': y, 'Z': z})

# print(xyzlevel)
ax = numpy.empty(len(xyzlevel))
ay = numpy.empty(len(xyzlevel))
az = numpy.empty(len(xyzlevel))
i = 0
for p in xyzlevel:
  ax[i] = p['X']
  ay[i] = p['Y']
  az[i] = p['Z']
  i = i + 1

# from xyz points, create z-interpolation function
# print(ax, ay, az)
zi = scipy.interpolate.Rbf(ax,ay,az, epsilon=2)




x = 0
y = 0
z = zi(x,y)
newZ = z
levelZ = z
e = 0
v = 0
cur_x = x
cur_y = y
cur_z = z
cur_e = e
absolute_mode = 1
absolute_extrude = 0
updown_mode = 0

layer = 0

if outputfile == "-":
  output_fd = sys.stdout
else:
  output_fd = open(os.path.expanduser(outputfile), "w")

with output_fd as f:
       for line in lines:
               if ";LAYER:" in line:
                    layer = int(line[7:])

               g = getValue(line, "M", None)
               if g != None and g > 81.999 and g < 82.001:
                 absolute_extrude = 1
               if g != None and g > 82.999 and g < 83.001:
                 absolute_extrude = 0
               
               g = getValue(line, "G", None)
               if g != None and g > 89.999 and g < 90.001:
                 absolute_mode = 1
               if g != None and g > 90.999 and g < 91.001:
                 absolute_mode = 0
               if g != None and g > 91.999 and g < 92.001:
                 x = getValue(line, "X", x)
                 y = getValue(line, "Y", y)
                 z = getValue(line, "Z", z)
                 e = getValue(line, "E", e)
                 cur_x = x
                 cur_y = y
                 cur_z = z
                 cur_e = e
               if g != None and g > 27.999 and g < 28.001:
                 x = 0
                 y = 0
                 z = 0

               if g != None and g > -0.001 and g < 1.001: # and (cur_z < toZ or zoffset != 0.0):
                       if absolute_mode > 0:
                         cur_x = getValue(line, "X", x)
                         cur_y = getValue(line, "Y", y)
                         cur_z = getValue(line, "Z", z)
                         dx = cur_x - x
                         dy = cur_y - y
                         dz = cur_z - z
                       else: # relative xyz mode
                         dx = getValue(line, "X", 0.0)
                         dy = getValue(line, "Y", 0.0)
                         dz = getValue(line, "Z", 0.0)
                         cur_x += dx
                         cur_y += dy
                         cur_z += dz

                       if absolute_extrude > 0:
                         cur_e = getValue(line, "E", e)
                         de = cur_e - e
                       else: # relative extrude
                         de = getValue(line, "E", 0.0)
                         cur_e += de

                       v = getValue(line, "F", None)
                       # apply adjustment, linearly reduced with layers

                       # todo: split one long G line into many short ones
                       xytravel = math.sqrt(dx*dx + dy*dy)
                       nsegments = 1
                       if xytravel > xymax and cur_z < toZ:
                         nsegments = 1+int(xytravel / xymax)
                         f.write((";LINE SPLIT %d SEGMENTS"%(nsegments))+"\n")

                       advance = 1.0/nsegments
                       for i in range(1,1+nsegments): # loop from 1 to nsegments
                           last_x = x
                           last_y = y
                           last_z = z
                           last_levelZ = levelZ
                           last_e = e
                           if i < nsegments:
                             x += dx * advance
                             y += dy * advance
                             z += dz * advance
                             e += de * advance
                           else:
                             x = cur_x
                             y = cur_y
                             z = cur_z
                             e = cur_e

                           zlevel = 0.0
                           if cur_z < toZ:
                             zlevel = zi(x,y) * (toZ-cur_z)/toZ
                           oldZ = newZ
                           newZ = cur_z + zoffset + zlevel
                           # for up-down split segment in 2
                           if (nsegments > 1 and newZ-oldZ < updown_threshold and updown < -0.00001) \
                           or (nsegments > 1 and newZ-oldZ > updown_threshold and updown > 0.00001):
                             # first half - Z updown
                             levelZ = newZ+updown
                             f.write("; UPDOWN\n");
                             f.write("G%d " %(g))
                             if absolute_mode > 0:
                               f.write("X%0.3f " %(x-dx*advance*0.5))
                               f.write("Y%0.3f " %(y-dy*advance*0.5))
                               f.write("Z%0.3f " %(levelZ))
                             else: # relative xyz
                               f.write("X%0.3f " %(dx*advance*0.5))
                               f.write("Y%0.3f " %(dy*advance*0.5))
                               f.write("Z%0.3f " %(levelZ-oldZ))
                               last_levelZ = levelZ
                             if absolute_extrude > 0:
                               f.write("E%0.5f " %(e-de*advance*0.5))
                             else:
                               f.write("E%0.5f " %(de*advance*0.5))
                             if v: f.write("F%0.1f " %(v))
                             f.write("\n")
                             updown_mode = 1
                             # second half follows as final Z
                           # if single segment (xytravel < xymax) then alternate Z
                           if (nsegments == 1 and updown_mode == 0 and newZ-oldZ < updown_threshold and updown < -0.00001) \
                           or (nsegments == 1 and updown_mode == 0 and newZ-oldZ > updown_threshold and updown > 0.00001):
                             alterZ = newZ+updown
                             updown_mode = 1
                             f.write("; ALTERNATE\n");
                           else:
                             alterZ = newZ
                             updown_mode = 0
                           levelZ = alterZ
                           f.write("G%d " %(g))
                           if absolute_mode > 0:
                             f.write("X%0.3f " %(x))
                             f.write("Y%0.3f " %(y))
                             f.write("Z%0.3f " %(levelZ))
                           else: # relative xyz
                             f.write("X%0.3f " %(x-last_x))
                             f.write("Y%0.3f " %(y-last_y))
                             f.write("Z%0.3f " %(levelZ-last_levelZ))
                           if absolute_extrude > 0:
                             f.write("E%0.5f " %(e))
                           else: # relative extrude
                             f.write("E%0.5f " %(e-last_e))
                           if v: f.write("F%0.1f " %(v))
                           f.write("\n")
               else:
                       f.write(line)
               

if view:
  # print(zi(50, 50))
  xrange = numpy.linspace(min(ax), max(ax), 100)
  yrange = numpy.linspace(min(ay), max(ay), 100)
  XI, YI = numpy.meshgrid(xrange, yrange)
  ZI = zi(XI, YI)
  matplotlib.pyplot.subplot(1,1,1)
  matplotlib.pyplot.pcolor(XI, YI, ZI, cmap=matplotlib.cm.jet)
  matplotlib.pyplot.title('RBF interpolation - multiquadrics')
  matplotlib.pyplot.colorbar()
  matplotlib.pyplot.show()
