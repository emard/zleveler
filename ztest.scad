for(i=[-4:4])
  for(j=[-4:4])
    if( i < -2 || i > 2 || j < -2 || j > 2 )
      translate([i*10,j*10,0])
        cylinder(d=5,h=1,$fn=20,center=true);

