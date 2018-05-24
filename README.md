# ZLeveler

Postprocess 3D printer G-Code output from Cura or Slic3r,
adjusting hotbed uneveness in Z-axis.

Adjustment of z-axis can be done manually
(without automatic Z-leveling hardware). 

Written in python

# Calibration file

Negative Z-value describes 'valley' (nozzle too far from surface).
Positive Z-value describes 'hill' (nozzle too close to surface).
Units are in mm.

Normal file should consist of all negative Z-values.
Adjust hotbed mechanically so that without zlevler
nozzle at Z=0 doesn't touch the hotbed surface.

Surface sampling: Move the nozzle accross the hotbed and 
count how many papers can be inserted between the nozle and hotbed.
Example: at point X=10 Y=20 you can insert 3 papers.
Assuming each paper is about 0.1 mm then you'd enter
a line:

    X10 Y20 Z-0.3

Example of complete file:

    cat ~/.zlevel.xyz

    X0   Y0   Z-0.1
    X25  Y0   Z-0.2
    X50  Y0   Z0
    X75  Y0   Z-0.1
    X100 Y0   Z-0.2

    X0   Y25  Z-0.3
    X25  Y25  Z-0.1
    X50  Y25  Z-0.2
    X75  Y25  Z-0.2
    X100 Y25  Z-0.1

    X0   Y50  Z-0.1
    X25  Y50  Z-0.2
    X50  Y50  Z-0.3
    X75  Y50  Z-0.2
    X100 Y50  Z0

    X0   Y75  Z-0.3
    X25  Y75  Z-0.2
    X50  Y75  Z-0.2
    X75  Y75  Z-0.3
    X100 Y75  Z-0.4

    X0   Y100 Z-0.2
    X25  Y100 Z-0.1
    X50  Y100 Z0
    X75  Y100 Z-0.1
    X100 Y100 Z-0.2

A 2D interpolation method "RBF" is used which is adaptive
so the calibration points can be randomly sampled.
You don't neccessary need to sample e.g. complete 5x5 grid 
over the hotbed.

Graphical view:

    ./zleveler.py -v1

![ZLEVEL](/pic/zlevel.png)

# Install

There are not many dependencies, and they are hopfully
easily obtainable:

    apt-get install python3-numpy python3-scipy python3-matplotlib

Works with Python2 or Python3.
Copy zleveler.py to any command search path

    chmod +x zleveler.py
    cp zleveler.py /usr/local/bin

Open repetierhost, select "curaengine" or "slic3r" slicer.
Printer Settings->Advanced->Post Slice FIlter
enter in the input box example:

    [zleveler.py --inputfile=#in --outputfile=#out --view=0 --updown_threshold=-0.001 --updown=-0.10 --zoffset=-0.03]
    [x] Run Filter after every Slice

# Options

     -n --toz=float

Apply Z-adjustment up to "toz" height [mm]. On each successive
layer Z-adjustment will decrease lineary. After "toz" height,
Z-adjuestment will not be applied because the layers
will become completely Z-flat. Default value 1 mm.

     -v --view=int

Graphical preview of the Z-adjustment values. After changing
Z-level file it is recommended to preview it graphically 
before sending g-code to the machine. If there's some
extreme value in ~/.zlevel.xyz file, it would be obvious.

     -z --zoffset=float

Global Z-offset [mm] adjusts nozzle to hotbed distance.

     -u --updown=float

Up-down mechanical gap of Z axis [mm]. This makes an important
workaround to let Z finish at same level when approaching from
either up or down.
"updown" value should be normally of opposite sign than the Z-direction in
which layers are built. When Z must travel in opposite direction
of the layers, "xymax" segment will be split into two halves.
In the first half of "xymax" segment, the Z-motor is driven to a
trip "below" the layer level. Because there is mechanical gap
nozzle will stay at layer level. On the other half the Z-motor is driven to the
layer level. For example, if layers go in positive Z direction, start
with small negative value like -0.07 and watch 1st layer. If filament is
applied too thick on Z-valley or detaches, gradually increase by 0.01 
into more negatve values until you see slight waves on filament desposted 
on 1st layer during correction of Z-valley on the hotbed.
Be careful because having this value too large will press nozzle down into
the hotbed.

    -t --updown_threshold=float

When Z-travel during a "xymax" segment is larger than this threshold value
[mm] then Z-downup correction will be applied. This value should normally
be of opposite sign than Z-direction in which layers are built.

    -x --xymax=float

When nozzle XY direction travels a distance longer than "xymax" [mm] then
the nozzle path in G-code will be split into N smaller segments, each
segment will be shorter than "xymax". Default value 10 mm.

    -i --inputfile=string

Input G-code file without Z-axis correction. Currently files from
"curaengine" and "slic3r" are known to work.
Default is "-" as stdin.

    -l --levelfile=string

Z-level file. Default is "~/.zlevel.xyz"

    -o --outputfile=string

Output G-code with Z-axis correction. Default is "-" as stdout.

# Automatic Z-probing

You don't need any special autoleveling support in firmware or hardware,
only a working Z-endstop switch and some G-code command (M119) which
reports endstop status.

Z-probing switch should be connected parallel to Z-endstop switch.
so triggering Z-probing switch will make the same signal as
Z-endstop switch.

Z-probing switch should be temporarily mounted on the hotend in order
to generate zlevel.xyz file and removed afterwards.

Python script "zprobe.py" will send G-codes to scan hotbed over a XY grid.
At each point of the grid it will lower the hotend until Z-probing
switch triggers, recording each point to a calibration file "zlevel.xyz".

During normal use, hotbed will keep its shape so Z-probing needs to be
obtained only once and will last for a very long time (months, years).

# Z-probing adapter

Openscad 3D-printable adapter "zprobe.scad" can hold small PCB
with Z-probing switch. Adapter has fittings to be properly mounted
on the hotend and also has hooks to temporarily hold fan assembly.
This adapter is suitable for "Fabrikator II mini".

On z-probe adapter mount small switch with help of some universal
PCB and screws. Try to position the switch so that when pressed it makes
contact "click" at approx the same xy position as the nozzle. z contact
position doesn't matter here. Take also care that this swich will replace
signal of z-stop switch and should be able mechanically go to xy home,
go down until itself is triggered for new z-stop and without breaking
leave this xyz-home position in y direction.

Connect 2.54 mm 2-pin header parallel to original z-stop switch.
Connect female 2.54 mm 2-pin socket on the z-probe switch with  wires,
of suitable length for z-probe to move around xy plate, wire should
be not too short not too long cca 20 cm.

To mount z-probe first raise up Z axis so nozzle is about 2-3 cm above printing plate.
Remove springs that hold fan assembly and carefully separate fan assembly
from the heatsink.. Check z-probe assembly 
(with the wired switch) trying to place it at the heatsink to test if it exactly
fits with its "back" side mathcing the space inside heatsink fins.

There are small holes for the springs at the zprobe. Place rear spring first at hole 
of the zprobe adapter, holding probe at some z-angle relative to heatsink so spring
doesn't tighten yet. Now holding heatsink, gently place zprobe adapter correctly
z-angle = 0, and rear spring will tighten. With help of some tool
carefully place front spring to zprobe front hole. Connect z-probe switch
wires to connector parallel to original z-stop switch. Return fan assembly into the 
"hands" of zprobe adapter it should exactly fit. Move motors manually to
check if everything is mechanically ok (nothing should break nor scratch)
before) letting machine use z-probe.

# Disclaimer

This code may have bugs and produce g-codes which lead to hardware error.
Be extra careful and always graphically preview generated g-code in 
e.g. repetierhost slice by slice before sending them to the machine.

It currently supports only absolute G code.
Relative G-code will be converted wrong and can damage the machine.

# Todo

    [x] Split long g-code into shorter ones --xymax=10.0
    [x] Option for global z-offset --zoffset=-0.5
    [x] Plot surface with matplotlib -v1
    [x] G92 support (change origin)
    [x] introduce xymin, don't half short segments
        but rather alternate them
    [x] default function as stdin/stdout filter
    [x] slic3r support (--tolayer -> --toz)
