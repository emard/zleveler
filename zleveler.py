#!/usr/bin/python
#Name: ZLeveler
#Info: Postprocess adjustment of Z-level for CuraEngine g-code
#Depend: GCode
#Type: postprocess
#Param: difference(float:15) Wave difference / amplitude(mm)
#Param: waves(float:4) Total waves
#Param: fromLayer(float:4) Start effect from (layer nr)
#Param: layerheight(float:0.2) Layerheight
#Param: centerX(float:102.5) Center of function X(mm)
#Param: centerY(float:102.5) Center of function Y(mm)


import re, math
import numpy
import scipy
import scipy.spatial
import scipy.interpolate

import inspect
import sys
import getopt

zScale = 1
startEffect = 0

def plugin_standalone_usage(myName):
 print "Usage:"
 print "  "+myName+" -n layers_to_adjust -f input_gcode_file -z zlevel_file -o output_gcode_file"
 sys.exit()

try:
 filename
except NameError:
 # Then we are called from the command line (not from cura)
 opts, extraparams = getopt.getopt(sys.argv[1:],'n:f:z:o',['tolayer=','inputfile=', 'zlevelfile=' 'outputfile='])

 toLayer = 6;

 filename="test.g"
 zlevelfile="zlevel.xyz"
 outfilename="output.g"

 for o,p in opts:
  if o in ['-n','--tolayer']:
   toLayer = int(p)
  elif o in ['-f','--inputfile']:
   filename = p
  elif o in ['-z','--zlevelfile']:
   zlevelfile = p
  elif o in ['-o','--outputfile']:
   outfilename = p
 if not filename:
  plugin_standalone_usage(inspect.stack()[0][1])

def getValue(line, key, default = None):
       if not key in line or (';' in line and line.find(key) > line.find(';')):
               return default
       subPart = line[line.find(key) + 1:]
       m = re.search('^[0-9]+\.?[0-9]*', subPart)
       if m == None:
               return default
       try:
               return float(m.group(0))
       except:
               return default

with open(filename, "r") as f:
       lines = f.readlines()

with open(zlevelfile, "r") as f:
       xyzlines = f.readlines()

xyzlevel = []
for xyzline in xyzlines:
       x = getValue(xyzline, 'X', None)
       y = getValue(xyzline, 'Y', None)
       z = getValue(xyzline, 'Z', None)
       if x != None and y != None and z != None:
         xyzlevel.append({'X': x, 'Y': y, 'Z': z})

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
zi = scipy.interpolate.Rbf(ax,ay,az, epsilon=2)
# print(zi(50, 50))

x = 0
y = 0
z = zi(x,y)
e = 0
v = 0

layer = 0

with open(outfilename, "w") as f:

       for line in lines:
               if ";LAYER:" in line:
                    layer = int(line[7:])
               
               g = getValue(line, "X", None)
               if g >= 0 and g <= 1 and layer < toLayer:
                       x = getValue(line, "X", y)
                       y = getValue(line, "Y", y)
                       z = getValue(line, "Z", z) 
                       e = getValue(line, "E", e)        
                       v = getValue(line, "F", None)
                       
                       newZ = z + zi(x,y)
                       
                       # todo: split one long G line into many short ones

                       f.write("G%d " %(g))
                       f.write("X%0.3f " %(x))
                       f.write("Y%0.3f " %(y))
                       f.write("Z%0.3f " %(newZ))
                       f.write("E%0.5f " %(e))
                       if v: f.write("F%0.1f " %(v))
                       f.write("\n")
                       
               else:
                       f.write(line)
               
