#! /usr/bin/python

from __future__ import unicode_literals

# gnis_summits.py

__author__ = "Roger Andre, July 2011"

import cgi
import sys
import math
from pymongo import Connection

def TileBounds(tx, ty, zoom):
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
  return [[minx_ll, miny_ll], [maxx_ll, maxy_ll]]


def getSummits(bbox):
  conn = Connection()
  db = conn.gnis
  collection = db.names
  bbox_summits = collection.find({'COORDS' : {'$within' : {'$box' : bbox}}, 'FEATURE_CLASS': "Summit"})
  print "Content-type: text/html\n\n"
  print '{"type":"FeatureCollection",'
  print ' "features": ['
  count = bbox_summits.count()
  i = 0
  for summit in bbox_summits:
    i += 1
    name = summit['FEATURE_NAME']
    coords = summit['COORDS']
    elev = summit['ELEV_IN_FT']
    print '''{"type": "Feature",
             "geometry":{"type":"Point", "coordinates":%s},
             "properties": {"name": "%s",
                            "elev": "%s"}
             }''' % (coords, "test_name", elev)
    if i < count:
      print ","
  print ']}'
                  

def main():
  # PULL OUT THE TMS VALUES
  form = cgi.FieldStorage()
  tms = form.getvalue('tile')
  #tms = "7,19,45" # UNCOMMENT FOR TESTING
  [Z,X,Y] = tms.split(",")

  # CONVERT TMS VALUES TO LL/UR BBOX
  bbox = TileBounds(int(X),int(Y),int(Z))

  # QUERY DATABASE AND PRINT OUT RESULTS
  getSummits(bbox)
  

if __name__ == '__main__':
  main()

