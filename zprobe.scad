yfan=35; // plastic contact to aluminium
zfan=24;
zalu=30; // aluminium height 30
yalu=3.0; // aluminium middle trench 3
xalu=1.0; // aluminium grip thickness
yhole=30; // vent hole
zhole=21;

xhook=5;
yhook=3.5;
zhook=3;
zhook_nozzle=48; // from hook center to nozzle height 38 mm
xnozzle=8.6; // from aluminum to nozzle center
thick=6; // desired thickness
fan_hook_clearance=1; // for the hook which will hold fan during zsensor
xfan_clearance=1;
xpcbh_start=3; // first screw hole X start
xpcbh=16; // pcb holder X
ypcbh=20;
zpcbh=4; // pcb holder Z thickness
xscrew=4*2.54; // x-screw distance
dscrew=1.9; // screw hole diameter
zscrew=7; // screw length
dspring=1.0; // spring diameter
trench=2.0; // spring trench depth

module switch_holder()
{
//translate([0,0,(zfan+(zhook_nozzle-zfan/2))/2])
  union()
  {
    // aluminium grips to fix z-level
    // vertical beam
    translate([-thick/2-xalu/2,0,0])
      cube([xalu,yalu,zalu],center=true);
    // lower horizontal
    translate([-thick/2-xalu/2,0,-zalu/2-yalu/2])
      difference()
      {
        cube([xalu,yfan,yalu],center=true);
        // 45 deg cut for printing
        translate([0,0,-yalu/2-xalu*sqrt(2)/4])
          rotate([0,-45,0])
            cube([xalu,yfan,yalu],center=true);
      }
    // Upper horizontal
    translate([-thick/2-xalu/2,0,+zalu/2+yalu/2])
      difference()
      {
        cube([xalu,yfan,yalu],center=true);
        // 45 deg cut for printing
        translate([0,0,-yalu/2-xalu*sqrt(2)/4])
          rotate([0,-45,0])
            cube([xalu,yfan,yalu],center=true);

      }
    // bottom positional helper
    if(0)
    translate([-thick/2-xalu/2,0,-48.5])
      cube([xalu,yfan,yalu],center=true);
    // fan positional helper
    if(0)
    translate([3.5,0,-5.5])
      cube([xalu,yfan,yalu],center=true);

      // plastic base under the fan
    translate([0,0,-(zfan/2)])
      difference()
      {
        union()
        {
          // main plate
          cube([thick,yfan,zhook_nozzle+zfan/2],center=true);
          // bottom PCB holder
    translate([xpcbh/2-zpcbh/2,0,-(zhook_nozzle+zfan/2)/2+zpcbh/2])
      difference()
      {
        union()
        {
          cube([xpcbh,ypcbh,zpcbh],center=true);
          // enforcement block
          translate([zpcbh+thick/2-xpcbh/2,0,zpcbh])
            difference()
            {
              cube([zpcbh+0.001,ypcbh+0.001,zpcbh+0.001],center=true);
              // 45 deg cut
              translate([zpcbh*0.7,0,zpcbh*0.7])
                rotate([0,45,0])
                  cube([zpcbh*2+0.002,ypcbh+0.002,zpcbh*2+0.002],center=true);
            }
        }
      }
        }
        // subtracting objects:
        // screw holes for PCB
        for(i=[0:1])
          translate([xpcbh_start-thick/2,0,-(zhook_nozzle+zfan/2)/2+zscrew/2])
            translate([i*xscrew,0,0])
              cylinder(d=dscrew,h=zscrew+0.001,$fn=10,center=true);

        // fan hole
        if(0)
        translate([0,0,zfan/2])
          difference()
          {
            cube([thick+0.001,yhole,zhole],center=true);
            // cut off top 45
            for(i=[-1:2:1])
            translate([0,i*yhole/2,zhole/2])
              rotate([45,0,0])
                cube([thick+0.002,15,15],center=true);
          }
      }
    // hooks
    xh=xhook*2+2*fan_hook_clearance+thick;
    zh=zhook+xh;
    // two hooks left-right
    for(i=[-1:2:1])
    {
      translate([-thick/2+xh/2,(yfan/2+yhook/2)*i,-zh/2+zhook/2])
        difference()
        {
          // full hook
          cube([xh,yhook,zh],center=true);
          union()
          {
              // cut to hold fan assembly
            translate([thick+xfan_clearance-xh/2+xhook/2+fan_hook_clearance/2,0,zh/2-zhook/2])
              cube([xhook+fan_hook_clearance,yhook+2*fan_hook_clearance,zhook+fan_hook_clearance],center=true);
              // cut for the spring
              // along Z
            translate([thick+xfan_clearance-xh/2+fan_hook_clearance/2-trench/2,-(yhook/2-dspring/2)*i,zh/2-zhook/2])
              cube([trench+0.001,dspring+0.001,zhook+0.001],center=true);
            // along X
            translate([thick+xfan_clearance-xh/2+fan_hook_clearance/2-xhook/2,-(yhook/2-dspring/2)*i,zh/2-zhook])
              cube([xhook+0.001,dspring+0.001,dspring+0.001],center=true);

          // easier print: big cut 45 from X
          translate([zh*1,0,-zh*0.66])
            rotate([0,45,0])
              cube([2*zh,2*zh,2*zh],center=true);
          // easier print: small cut 45 from Y
          translate([zh*0,zh*i,-zh*0.82])
            rotate([45,0,0])
              cube([2*zh,2*zh,2*zh],center=true);

          }
        }
    }
    
  }
}

switch_holder();
