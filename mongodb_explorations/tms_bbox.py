#! /usr/bin/python

import cgi
import sys
import math

__author__ = "Roger Andre, July 2011"

'''Python CGI script to return JSON tile boundaries from a Polymaps TMS request.

   To use, add the following line to your polymaps html file:
      .add(po.geoJson().url("http://localhost/cgi-bin/tms_bbox.py?tile={Z},{X},{Y}").id("bbox"))
  
   (Also add CSS style for "bbox" layer in html, like:
      #bbox path {
      stroke: #FF0;
      stroke-width: 1.5px;
      vector-effect: non-scaling-stroke;
      fill: none;
      }

   Modified from code at http://geojason.info/tag/polymaps/
'''


def TileBounds(tx, ty, zoom):
  # Returns bounds of the given tile in EPSG:4326 coordinates
  ty = ((1 << zoom) - ty - 1)
	
  # Pixels to Meters
  # Converts pixel coordinates in given zoom level of pyramid to EPSG:900913
  originShift = 20037508.342789244
  # resolution = (meters/pixel) for given zoom level (measured at Equator)
  resolution = 156543.03392804062 / (2**zoom)
  minx_meters = ( tx * 256 ) * resolution - originShift
  miny_meters = ( ty * 256 ) * resolution - originShift
  maxx_meters = ( ( tx + 1 ) * 256 ) * resolution - originShift
  maxy_meters = ( ( ty + 1 ) * 256 ) * resolution - originShift

  # Meters to Lat/Lon
  # Converts XY point from Spherical Mercator EPSG:900913 to lat/lon in WGS84 Datum
  minx_ll = (minx_meters / originShift) * 180.0
  miny_ll = (miny_meters / originShift) * 180.0
  maxx_ll = (maxx_meters / originShift) * 180.0
  maxy_ll = (maxy_meters / originShift) * 180.0
	
  miny_ll = 180 / math.pi * (2 * math.atan( math.exp( miny_ll * math.pi / 180.0)) - math.pi / 2.0)
  maxy_ll = 180 / math.pi * (2 * math.atan( math.exp( maxy_ll * math.pi / 180.0)) - math.pi / 2.0)
	
  return '''{"type":"FeatureCollection","features":[{"geometry":{"type":"Polygon","coordinates":[[[%.6f,%.6f],[%.6f,%.6f],[%.6f,%.6f],[%.6f,%.6f],[%.6f,%.6f]]]}}]}''' % (minx_ll, miny_ll, 
                  minx_ll, maxy_ll, 
                  maxx_ll, maxy_ll, 
                  maxx_ll, miny_ll, 
                  minx_ll, miny_ll)


def main():
  # Create instance of FieldStorage 
  form = cgi.FieldStorage() 
  # PARSE TMS VALUES FROM QUERY
  try:
    tms = form.getvalue('tile') 
    [Z,X,Y] = tms.split(",")
  except:
    error = sys.exc_info()  
    log = open('tms_bbox.log', 'a')
    log.write(error)

  # WRITE OUT TO WEB
  print "Content-type: text/html\n\n"
  print TileBounds(int(X),int(Y),int(Z))
  

if __name__ == '__main__':
  main()
