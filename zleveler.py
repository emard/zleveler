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
   ['tolayer=','view=','zoffset=','updown=','updown_threshold=','xymax=','inputfile=','levelfile=','outputfile=']
 )

 toLayer = 6;

 inputfile="input.gcode"
 zlevelfile="~/.zlevel.xyz"
 outputfile="output.gcode"
 view=0
 zoffset=0.0
 updown_threshold=0.0 # start experimenting with -0.03
 updown=0.0 # start experimenting with -0.07
 xymax=10.0

 for o,p in opts:
  if o in ['-n','--tolayer']:
   toLayer = int(p)
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

with open(os.path.expanduser(inputfile), "r") as f:
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
e = 0
v = 0
absolute_mode = 0

layer = 0

with open(os.path.expanduser(outputfile), "w") as f:

       for line in lines:
               if ";LAYER:" in line:
                    layer = int(line[7:])
               
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
               
               if g != None and g > -0.001 and g < 1.001 and (layer < toLayer or zoffset != 0.0) and absolute_mode > 0:
                       cur_x = getValue(line, "X", x)
                       cur_y = getValue(line, "Y", y)
                       cur_e = getValue(line, "E", e)
                       dx = cur_x - x
                       dy = cur_y - y
                       de = cur_e - e
                       z = getValue(line, "Z", z)
                       v = getValue(line, "F", None)
                       # apply adjustment, linearly reduced with layers

                       # todo: split one long G line into many short ones
                       xytravel = math.sqrt(dx*dx + dy*dy)
                       nsegments = 1
                       if xytravel > xymax and layer < toLayer:
                         nsegments = 1+int(xytravel / xymax)
                         f.write((";LINE SPLIT %d SEGMENTS"%(nsegments))+"\n")

                       advance = 1.0/nsegments
                       for i in range(1,1+nsegments): # loop from 1 to nsegments
                           if i < nsegments:
                             x += dx * advance
                             y += dy * advance
                             e += de * advance
                           else:
                             x = cur_x
                             y = cur_y
                             e = cur_e

                           zlevel = 0.0
                           if layer < toLayer:
                             zlevel = zi(x,y) * (toLayer-layer)/toLayer
                           oldZ = newZ
                           newZ = z + zoffset + zlevel
                           # for up-down split segment in 2
                           if (newZ-oldZ < updown_threshold and updown < 0.00001) \
                           or (newZ-oldZ > updown_threshold and updown > 0.00001):
                             # first half - Z updown
                             f.write("; UPDOWN\n");
                             f.write("G%d " %(g))
                             f.write("X%0.3f " %(x-dx*advance*0.5))
                             f.write("Y%0.3f " %(y-dy*advance*0.5))
                             f.write("Z%0.3f " %(newZ+updown))
                             if e: f.write("E%0.5f " %(e-de*advance*0.5))
                             if v: f.write("F%0.1f " %(v))
                             f.write("\n")
                             # second half follows as final Z
                           f.write("G%d " %(g))
                           f.write("X%0.3f " %(x))
                           f.write("Y%0.3f " %(y))
                           f.write("Z%0.3f " %(newZ))
                           if e: f.write("E%0.5f " %(e))
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
