"""

"""

from google.appengine.ext import ndb

class Score(ndb.Model):
	member_no = ndb.IntegerProperty()
	date = ndb.DateProperty()
	handicap = ndb.IntegerProperty()
	scratch = ndb.IntegerProperty()
	nett = ndb.IntegerProperty()