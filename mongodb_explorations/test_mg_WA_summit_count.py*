#! /usr/bin/python

import unittest
from pymongo import Connection


class TestMongoQuery(unittest.TestCase):

  def test_GetStateSummits(self):
    conn = Connection()
    db = conn.gnis
    collection = db.NationalFile
    wa_summits = collection.find({'STATE_ALPHA': "WA", 'FEATURE_CLASS': "Summit"}).count()
    self.assertEqual(wa_summits, 2687)

if __name__ == '__main__':
    unittest.main()
