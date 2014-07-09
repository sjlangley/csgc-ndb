"""
"""

from google.appengine.ext import ndb

class Club(ndb.Model):
  name = ndb.StringProperty(required=True)


class Course(ndb.Model):
  name = ndb.StringProperty()
  club = ndb.KeyProperty(kind=Club)


class Tee(ndb.Model):
  name = ndb.StringProperty(required=True)
  course = ndb.KeyProperty(kind=Course, required=True)
  par = ndb.IntegerProperty(required=True)
  slope = ndb.IntegerProperty()
  amcr = ndb.IntegerProperty()
  distance = ndb.IntegerProperty()


class Member(ndb.Model):
  first_name = ndb.StringProperty(required=True)
  last_name = ndb.StringProperty(required=True)
  nick_name = ndb.StringProperty()
  email = ndb.StringProperty()
  member_no = ndb.IntegerProperty()
  phone_number1 = ndb.StringProperty()
  phone_number2 = ndb.StringProperty()


class Score(ndb.Model):
  member = ndb.KeyProperty(kind=Member)
  tee = ndb.KeyProperty(kind=Tee)
  date = ndb.DateProperty(required=True)
  handicap = ndb.IntegerProperty()
  scratch = ndb.IntegerProperty(required=True)
  nett = ndb.IntegerProperty(required=True)
  points = ndb.IntegerProperty()


class Match(ndb.Model):
  date = ndb.DateProperty()
  tee = ndb.KeyProperty(kind=Tee)
  scores = ndb.KeyProperty(kind=Score, repeated=True)
  winner = ndb.KeyProperty(kind=Member, required=True)
  runner_up = ndb.KeyProperty(kind=Member)
  third = ndb.KeyProperty(kind=Member)
  fourth = ndb.KeyProperty(kind=Member)

  # Individual Hole Winners

