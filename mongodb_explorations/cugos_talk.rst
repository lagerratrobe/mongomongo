-----------------------------------------
Messing About with MongoDB (and Polymaps)
-----------------------------------------

Why?
----

- Because they're different from the usual web mapping geospatial stack
- Because there's still a great deal of buzz about NoSQL databases
- Because I was curious about JSON tiles and CSS map styling

Why MongoDB?
------------
- Written in C++
- Uses a binary data storage format (BSON)
- Has rudimentary support for spatial data
- Saw Roger Bodamer from 10gen speak at a conference

Why Polymaps?
-------------
- Like their philosophy about browsers
- Like their philosophy on map projections - Spherical Mercator is good enough!
- Wanted to explore the SVG display of JSON tiles

So what's the goal?
-------------------
- Polymaps map of U.S.A. Mountain Summits
- Data from Geographic Names Information System (GNIS)
- Data stored in MongoDB database

Mongo Stuff
-----------
**1. Get data from http://geonames.usgs.gov/**
	- NationalFile_20110613.zip, contains 282 MB .txt file
	- 2,183,268 records that contain the following feature classes:
		*Airport Arch Area Arroyo Bar Basin Bay Beach Bench Bend Bridge Building Canal
		Cape Cemetery Census Channel Church Civil Cliff Crater Crossing Dam Falls Flat
		Forest Gap Glacier Gut Harbor Hospital Island Isthmus Lake Lava Levee Locale
                Military Mine Oilfield Park Pillar Plain Populated Place Post Office Range Rapids
		Reserve Reservoir Ridge School Sea Slope Spring Stream Summit Swamp Tower Trail 
		Tunnel Valley Well Woods*
	- Records look like this (some fields omitted for clarity):
		**FEATURE_ID|FEATURE_NAME|FEATURE_CLASS|STATE_ALPHA|STATE_NUMERIC|COUNTY_NAME|COUNTY_NUMERIC|PRIM_LAT_DEC|PRIM_LONG_DEC|ELEV_IN_M|ELEV_IN_FT**
		**399|Agua Sal Creek|Stream|AZ|04|Apache|001|36.4611122|-109.4784394|1645|5397**

**2. Install MongoDB** (I followed instructions for Ubuntu install at http://www.mongodb.org/display/DOCS/Ubuntu+and+Debian+packages.)

Start Mongodb as a daemon: ::

  $ mongod --fork --dbpath /usr/local/mongodb/db/ --logpath /usr/local/mongodb/log/mongodb.log --logappend
  forked process\: 3018
  all output going to: /usr/local/mongodb/log/mongodb.log

**3. Create a new database:**

Databases are created lazily the first time data is inserted.  In other words, if you specify the name of a DB and a collection that don't currently exist as part of your upload process, they will automatically be created for you.

**(A brief segway into MongoDB structure)**

MongoDB is a *document* database that contains *Collections*, so the structure looks like this:

- Database = "gnis"
	- Collection = "names"
		- Document = json record:
			**{_ID: 399, FEATURE_NAME: "Agua Sal Creek", FEATURE_CLASS: "Stream", STATE_ALPHA: "AZ", STATE_FIPS: 04, COUNTY_NAME: "Apache",**
			**COUNTY_FIPS: "001", COORDS: [-109.4784394,36.4611122], ELEV_IN_FT: "5397"}**

**3. Upload records and create collection and database:** ::

  $ mongoimport -h localhost -d gnis -c names --file mongo_gnis_upload.json --stopOnError

**4. Do a query to test that everything works as it should:** ::

  $ mongo gnis
  MongoDB shell version: 1.8.2
  connecting to: gnis
  > db.names.find({FEATURE_NAME: 'Mount Saint Helens', STATE_ALPHA: 'WA'})       
  { "_id" : ObjectId("4e262106d7a99b7db41a4919"), "_ID" : 1525360, "FEATURE_NAME" : "Mount Saint Helens", "FEATURE_CLASS" : "Summit", "STATE_ALPHA" : "WA", "STATE_FIPS" : 53, "COUNTY_NAME" : "Skamania", "COUNTY_FIPS" : "059", "COORDS" : [ -122.1944, 46.1912 ], "ELEV_IN_FT" : "8356" }


Polymaps Stuff
--------------

**1. Sample of Polymaps JSON tile requests from apache access.log:** ::

  "GET /cgi-bin/foo/7/19/45.json 
  "GET /cgi-bin/foo/7/18/45.json
  "GET /cgi-bin/foo/7/18/44.json
  "GET /cgi-bin/foo/7/23/45.json
  "GET /cgi-bin/foo/7/22/45.json
  "GET /cgi-bin/foo/7/21/45.json
  "GET /cgi-bin/foo/7/23/44.json
  "GET /cgi-bin/foo/7/22/44.json
  "GET /cgi-bin/foo/7/20/44.json
  "GET /cgi-bin/foo/7/21/44.json
  "GET /cgi-bin/foo/7/19/44.json
  "GET /cgi-bin/foo/7/23/43.json
  "GET /cgi-bin/foo/7/22/43.json
  "GET /cgi-bin/foo/7/21/43.json
  "GET /cgi-bin/foo/7/20/43.json
  "GET /cgi-bin/foo/7/19/43.json
  "GET /cgi-bin/foo/7/18/43.json

**2. Sample of what Polymaps expects in return:** ::

  {"type":"FeatureCollection",
          "features":[{"geometry":{"type":"Polygon",
                                   "coordinates":[[[-126.562500,45.089036],
                                                   [-126.562500,47.040182],
                                                   [-123.750000,47.040182],
                                                   [-123.750000,45.089036],
                                                   [-126.562500,45.089036]
                                                 ]]
                                  }
                      },
                      {"geometry":{"type":"Polygon",
                                   "coordinates":[[[-129.375000,45.089036],
                                                   [-129.375000,47.040182],
                                                   [-126.562500,47.040182],
                                                   [-126.562500,45.089036],
                                                   [-129.375000,45.089036]
                                                 ]]
                                  }
                      }
                     ]
  }

**3. So the key is to convert the Z,X,Y TMS request into a lat/lon bounding box.  Here is a cgi script that does that, and returns the bbox as JSON polygons:**

`mongomongo/mongodb_explorations/tms_bbox.py  <https://github.com/lagerratrobe/mongomongo/blob/master/mongodb_explorations/tms_bbox.py>`_.

**4. And this is what it looks like when you point Polymaps at that script:**

`Dynamic tile bbox layer <http://www.macrogis.net/bbox_polymaps.html>`_.


Back to Mongodb, With Python Glue
---------------------------------

**1. So now all we need to do is use the BBOX extents to do a spatial query in Mongo.**

Query looks like this from the mongo shell: ::

  $ mongo gnis
  MongoDB shell version: 1.8.2
  connecting to: gnis
  > box = [[-126.562500,45.089036], [-123.750000,47.040182]]
  [ [ -126.5625, 45.089036 ], [ -123.75, 47.040182 ] ]
  > db.names.find({"COORDS" : {"$within" : {"$box" : box}}, FEATURE_CLASS: "Summit"}, {FEATURE_NAME: 1, ELEV_IN_FT: 1})
  { "_id" : ObjectId("4e2620f8d7a99b7db4146cec"), "FEATURE_NAME" : "Harlocker Hill", "ELEV_IN_FT" : "0" }
  { "_id" : ObjectId("4e2620f8d7a99b7db414a349"), "FEATURE_NAME" : "Neskowin Crest", "ELEV_IN_FT" : "194" }
  { "_id" : ObjectId("4e2620f8d7a99b7db414a105"), "FEATURE_NAME" : "Miles Mountain", "ELEV_IN_FT" : "1220" }
  { "_id" : ObjectId("4e2620f8d7a99b7db414934a"), "FEATURE_NAME" : "Mount Gauldy", "ELEV_IN_FT" : "2165" }
  { "_id" : ObjectId("4e2620f8d7a99b7db4149d06"), "FEATURE_NAME" : "Little Hebo", "ELEV_IN_FT" : "2270" }
  { "_id" : ObjectId("4e2620f8d7a99b7db41479b0"), "FEATURE_NAME" : "Alderman Butte", "ELEV_IN_FT" : "121" }
  { "_id" : ObjectId("4e2620f8d7a99b7db414ab23"), "FEATURE_NAME" : "Round Top", "ELEV_IN_FT" : "1099" }
  { "_id" : ObjectId("4e2620f8d7a99b7db41485a4"), "FEATURE_NAME" : "Buzzard Butte", "ELEV_IN_FT" : "1683" }
  { "_id" : ObjectId("4e2620f8d7a99b7db414b009"), "FEATURE_NAME" : "South Point", "ELEV_IN_FT" : "3133" }
  { "_id" : ObjectId("4e2620f8d7a99b7db4149645"), "FEATURE_NAME" : "Mount Hebo", "ELEV_IN_FT" : "3140" }
  { "_id" : ObjectId("4e2620f8d7a99b7db4146c15"), "FEATURE_NAME" : "Green Hill", "ELEV_IN_FT" : "331" }
  { "_id" : ObjectId("4e2620f8d7a99b7db4147738"), "FEATURE_NAME" : "Balmer Hill", "ELEV_IN_FT" : "486" }
  { "_id" : ObjectId("4e2620f7d7a99b7db4143c7a"), "FEATURE_NAME" : "Doty Hill", "ELEV_IN_FT" : "1972" }
  { "_id" : ObjectId("4e2620f8d7a99b7db4146c1e"), "FEATURE_NAME" : "Craig Mountain", "ELEV_IN_FT" : "2008" }
  { "_id" : ObjectId("4e2620f7d7a99b7db4143fb0"), "FEATURE_NAME" : "Foley Peak", "ELEV_IN_FT" : "2260" }
  { "_id" : ObjectId("4e2620f7d7a99b7db4144e49"), "FEATURE_NAME" : "Neahkahnie Mountain", "ELEV_IN_FT" : "1598" }
  { "_id" : ObjectId("4e2620f8d7a99b7db4147c78"), "FEATURE_NAME" : "Round Mountain", "ELEV_IN_FT" : "764" }
  { "_id" : ObjectId("4e2620f8d7a99b7db4147a99"), "FEATURE_NAME" : "Double Peak", "ELEV_IN_FT" : "978" }
  { "_id" : ObjectId("4e2620f8d7a99b7db41463f0"), "FEATURE_NAME" : "Bald Mountain", "ELEV_IN_FT" : "755" }
  { "_id" : ObjectId("4e262115d7a99b7db420571c"), "FEATURE_NAME" : "Clark's Mountain", "ELEV_IN_FT" : "1253" }
  has more

**2. Use the Python API for MongoDB (pymongo) to take the BBOX we calculate from each TMS request and use it to query the database for summits in that BBOX:** 

Script that does this is `mongomongo/mongodb_explorations/gnis_summits.py <https://github.com/lagerratrobe/mongomongo/blob/master/mongodb_explorations/gnis_summits.py>`_.

**3. Put it all together in a map:** 

`GNIS Summits <http://www.macrogis.net/summits_polymaps.html>`_.

Next Steps
----------

* Scale dependent filtering of features
* Dynamic control of feature display from Web page
* More research on MongoDB `spatial querying capability <http://www.mongodb.org/display/DOCS/Geospatial+Indexing>`_.
* Storage of lines and polygons in Mongo (Can we index these for spatial searches?)
* Performance optimization, cgi is probably alot slower than it could be
* Plugging MongoDB into GDAL and/or MapServer
