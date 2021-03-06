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
  initial_handicap = ndb.FloatProperty()
  inactive = ndb.BooleanProperty(default=False)

# Keep track of the members handicap and when it was last calculated, to
# make is faster to lookup handicaps if they've already been calculated.
class MemberHandicap(ndb.Model):
  member = ndb.KeyProperty(kind=Member)
  current_handicap = ndb.FloatProperty()
  current_handicap_date = ndb.DateProperty()


class Score(ndb.Model):
  member = ndb.KeyProperty(kind=Member)
  tee = ndb.KeyProperty(kind=Tee)
  date = ndb.DateProperty(required=True)
  # This is the handicap that was used for this round.
  handicap = ndb.IntegerProperty()
  scratch = ndb.IntegerProperty(required=True)
  nett = ndb.IntegerProperty(required=True)
  points = ndb.IntegerProperty()


class Match(ndb.Model):
  date = ndb.DateProperty()
  tee = ndb.KeyProperty(kind=Tee)
  scores = ndb.KeyProperty(kind=Score, repeated=True)
  winner = ndb.KeyProperty(kind=Member)
  runner_up = ndb.KeyProperty(kind=Member)
  third_place = ndb.KeyProperty(kind=Member)
  fourth_place = ndb.KeyProperty(kind=Member)
  closest_pin_4th = ndb.KeyProperty(kind=Member)
  drive_chip_5th = ndb.KeyProperty(kind=Member)
  drive_chip_6th = ndb.KeyProperty(kind=Member)
  closest_pin_9th = ndb.KeyProperty(kind=Member)
  closest_pin_10th = ndb.KeyProperty(kind=Member)
  closest_pin_16th = ndb.KeyProperty(kind=Member)
  closest_pin_17th = ndb.KeyProperty(kind=Member)
  longest_drive_0_18 = ndb.KeyProperty(kind=Member)
  longest_drive_19plus = ndb.KeyProperty(kind=Member)
  longest_drive_60over = ndb.KeyProperty(kind=Member)


class Config(ndb.Model):
  win_score_adjustment = ndb.IntegerProperty()
  handicap_mulitplier = ndb.FloatProperty()


  # Individual Hole Winners

