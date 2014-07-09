"""

"""

from datetime import *
import json
import urllib
import webapp2

from models import *

# Club Management
class AddClub(webapp2.RequestHandler):
  """Add a new club to the database."""

  def post(self):
    """Everything comes in via the post."""

    failure_heading = None
    failure_message = None

    club_name = self.request.get('clubNameInput')

    courses = []
    for i in xrange(2):
      course_name = self.request.get('courseNameInput_' + str(i))
      tees = []
      for j in xrange(4):
        tee_name = self.request.get('teeNameInput_'+str(i)+'_'+str(j))
        tee_amcr = self.request.get('teeAmcrInput_'+str(i)+'_'+str(j))
        slope = self.request.get('teeSlopeInput_'+str(i)+'_'+str(j))
        dist = self.request.get('teeDistanceInput_'+str(i)+'_'+str(j))
        par = self.request.get('teeParInput_'+str(i)+'_'+str(j))
        if tee_name and par:
          tees.append({
            'name': tee_name,
            'amcr': tee_amcr,
            'slope': slope,
            'distance': int(dist),
            'par': int(par)
          })
      if tees:
        courses.append({
          'name': course_name,
          'tees': tees
        })

    club_data = {
      'name': club_name,
      'courses': courses,
    }

    # failure message
    heading = "Could Not Add New Club"
    message = None
    if not club_data['name']:
      message = "Club Name Not Speficied"
    elif not club_data['courses']:
      message = "No courses specified"
    else:
      club = Club(name=club_data['name'])
      club.put()

      for course_data in club_data['courses']:
        course = Course(name=course_data['name'], club=club.key)
        course.put()

        for tee_data in course_data['tees']:
          tee = Tee(name=tee_data['name'],
              course=course.key,
              par=tee_data['par'])
          if tee_data['amcr']:
            tee.amcr = int(tee_data['amcr'])
          if tee_data['slope']:
            tee.slope = int(tee_data['slope'])
          if tee_data['distance']:
            tee.distance = int(tee_data['distance'])

          tee.put()

    if message:
      query = urllib.urlencode({'heading': heading, 'message': message})
      self.redirect('/failure?' + query)
    else:
      dest = '/list-club-general?club=%s&added' % club.key.urlsafe()
      self.redirect(dest)


class ListClub(webapp2.RequestHandler):
  """List a club in the database."""

  def get(self):

    club_key = self.request.get('club_key', None)

    if club_key:
      self._get_club_by_key(ndb.Key(urlsafe=club_key))
    else:
      self._get_all_clubs()

  def _get_club_by_key(self, club_key):
    """Return club details from a given key."""
    club = club_key.get()
    result = [{
      'name': club.name,
      'key': club.key.urlsafe(),
      'courses': self._get_courses_for_club(club.key)
    }]
    self.response.content_type = 'application/json';
    self.response.out.write(json.dumps(result))

  def _get_all_clubs(self):
    result = []
    club_query = Club.query().order(Club.name)
    for club in club_query:
      result.append({
        'name': club.name,
        'key': club.key.urlsafe(),
        'courses': self._get_courses_for_club(club.key)
      })

    self.response.content_type = 'application/json';
    self.response.out.write(json.dumps(result))


  def _get_courses_for_club(self, club_key):
    """Return a list of courses for a given club."""
    result = []
    course_query = Course.query(Course.club == club_key)
    for course in course_query:
      result.append({
        'name': course.name,
        'tees': self._get_tees_for_course(course.key)
      })
    return result

  def _get_tees_for_course(self, course_key):
    """Return the list of tees for a given course."""
    result = []
    tee_query = Tee.query(Tee.course == course_key)
    for tee in tee_query:
      result.append({
        'name': tee.name,
        'amcr': tee.amcr,
        'slope': tee.slope,
        'distance': tee.distance,
        'par': tee.par,
        'key': tee.key.urlsafe()
      })
    return result


# Member Management
class AddMember(webapp2.RequestHandler):
  """ """

  def post(self):
    """Add members to the database."""
    form_size = int(self.request.get('form_size', default_value=10))
    member_list = []

    for i in xrange(form_size):
      first_name = self.request.get('first_name' + str(i))
      last_name = self.request.get('last_name' + str(i))
      email = self.request.get('email' + str(i), default_value=None)
      member_no = self.request.get('member_no' + str(i), default_value=0)
      phone_number1 = self.request.get('phone_number1' + str(i), default_value=None)
      phone_number2 = self.request.get('phone_number2' + str(i), default_value=None)
      handicap = self.request.get('hc_' + str(i), default_value=None)

      if first_name and last_name:
        member = Member(first_name=first_name, last_name=last_name,
            email=email, phone_number1=phone_number1,
            phone_number2=phone_number2, member_no=member_no)
        if handicap:
          member.initial_handicap = float(handicap)

        member_list.append(member)

    member_keys = ndb.put_multi(member_list)

    result = {
      'member_keys': [key.urlsafe() for key in member_keys]
    }

    self.response.content_type = 'application/json';
    self.response.out.write(json.dumps(result))


class ListMembers(webapp2.RequestHandler):
  """   """

  def get(self):
    with_scores = self.request.get('with_scores', default_value=None)
    result = []
    query = Member.query().order(Member.member_no)
    for member in query:
      member_data = {
        'key': member.key.urlsafe(),
        'first_name': member.first_name,
        'last_name' : member.last_name,
        'email': member.email,
        'member_no': member.member_no,
        'phone_numbers': [
          member.phone_number1,
          member.phone_number2,
        ],
        'last_match': _get_last_match_for_member(member.key),
      }
      if with_scores:
        member_data['scores'] = _get_scores_for_member(member.key)

      result.append(member_data)

    self.response.content_type = 'application/json';
    self.response.out.write(json.dumps(result))


# Score Management
class GetScores(webapp2.RequestHandler):
  """Retrieves all of the scores for a single member."""

  def get(self):
    member_key = self.request.get('member_key', default_value=None)
    key = ndb.Key(urlsafe=member_key)
    member = key.get()

    result = [{
      'member_key': _get_scores_for_member(member.key())
    }]

    self.response.content_type = 'application/json';
    self.response.out.write(json.dumps(result))


class DeleteScore(webapp2.RequestHandler):
  """ """

  def get(self):
    pass

# Match Management
class AddMatch(webapp2.RequestHandler):

  def post(self):
    match_result = self._extract_match_results()

    tee = ndb.Key(urlsafe=match_result['tee_key'])
    date_object = datetime.strptime(match_result['date'], '%Y-%m-%d')
    match_date = date_object.date()

    scores = []
    for score in match_result['scores']:
      scores.append(
        Score(member=ndb.Key(urlsafe=score['player_key']),
          tee=tee,
          date=match_date,
          scratch=score['score'],
          handicap=score['hc'],
          nett=score['nett'],
          points=score['pts'],
        )
      )

    score_keys = ndb.put_multi(scores)
    match = Match(date=match_date, tee=tee, scores=score_keys)

    if match_result['winner']:
      match.winner = ndb.Key(urlsafe=match_result['winner'])

    if match_result['runner_up']:
      match.runner_up = ndb.Key(urlsafe=match_result['runner_up'])

    if match_result['third_place']:
      match.third_place = ndb.Key(urlsafe=match_result['third_place'])

    if match_result['fourth_place']:
      match.fourth_place = ndb.Key(urlsafe=match_result['fourth_place'])

    if match_result['closest_pin_4th']:
      match.closest_pin_4th = ndb.Key(urlsafe=match_result['closest_pin_4th'])

    if match_result['drive_chip_5th']:
      match.drive_chip_5th = ndb.Key(urlsafe=match_result['drive_chip_5th'])

    if match_result['drive_chip_6th']:
      match.drive_chip_6th = ndb.Key(urlsafe=match_result['drive_chip_6th'])

    if match_result['closest_pin_9th']:
      match.closest_pin_9th = ndb.Key(urlsafe=match_result['closest_pin_9th'])

    if match_result['closest_pin_10th']:
      match.closest_pin_10th = ndb.Key(urlsafe=match_result['closest_pin_10th'])

    if match_result['closest_pin_16th']:
      match.closest_pin_16th = ndb.Key(urlsafe=match_result['closest_pin_16th'])

    if match_result['closest_pin_17th']:
      match.closest_pin_10th = ndb.Key(urlsafe=match_result['closest_pin_17th'])

    if match_result['longest_drive_0_18']:
      match.longest_drive_0_18 = ndb.Key(urlsafe=match_result['longest_drive_0_18'])

    if match_result['longest_drive_19plus']:
      match.longest_drive_19plus = ndb.Key(urlsafe=match_result['longest_drive_19plus'])

    if match_result['longest_drive_60over']:
      match.longest_drive_60over = ndb.Key(urlsafe=match_result['longest_drive_60over'])

    match.put()

    self.redirect('/show-match-result?match_key=%s' % match.key.urlsafe())


  def _extract_match_results(self):
    result = {
      'tee_key': self.request.get('teeRadio'),
      'date': self.request.get('game_date'),
      'winner': self.request.get('winner'),
      'runner_up': self.request.get('runner_up'),
      'third_place': self.request.get('third_place'),
      'fourth_place': self.request.get('fourth_place'),
      'closest_pin_4th': self.request.get('closest_pin_4th'),
      'drive_chip_5th': self.request.get('drive_chip_5th'),
      'drive_chip_6th': self.request.get('drive_chip_6th'),
      'closest_pin_9th': self.request.get('closest_pin_9th'),
      'closest_pin_10th': self.request.get('closest_pin_10th'),
      'closest_pin_16th': self.request.get('closest_pin_16th'),
      'closest_pin_17th': self.request.get('closest_pin_17th'),
      'longest_drive_0_18': self.request.get('longest_drive_0_18'),
      'longest_drive_19plus': self.request.get('longest_drive_19plus'),
      'longest_drive_60over': self.request.get('longest_drive_60over'),
    }

    scores = []
    for i in xrange(30):
      player_key = self.request.get('score_' + str(i), default_value='none')
      score = self.request.get('score_value_' + str(i))
      hc = self.request.get('hc_value_' + str(i))
      nett = self.request.get('nett_value_' + str(i))
      pts = self.request.get('pts_value_' + str(i))

      if player_key != 'none':
        scores.append({
          'player_key': player_key,
          'score': int(score),
          'hc': int(hc),
          'nett': int(nett),
          'pts': int(pts),
        })

    result['scores'] = scores
    return result


class GetMatch(webapp2.RequestHandler):

  def get(self):

    match_key = self.request.get('match_key')

    if match_key:
      result = self._return_detailed_match(match_key)
    else:
      result = self._return_match_summaries()

    self.response.content_type = 'application/json';
    self.response.out.write(json.dumps(result))



  def _return_detailed_match(self, match_key):

    key = ndb.Key(urlsafe=match_key)
    match = key.get()
    tee = _get_tee_by_key(match.tee)
    scores = ndb.get_multi(match.scores)

    result = {
      'date': match.date.strftime('%Y-%m-%d'),
      'score_count': len(match.scores),
      'tee': {
        'name': tee['name'],
        'par': tee['par'],
      },
    }

    score_data = []
    for score in scores:
      score_data.append({
        'member': _get_member_by_key(score.member),
        'scratch': score.scratch,
        'nett': score.nett,
        'points': score.points,
        'handicap': score.handicap,
      })

    result['scores'] = score_data
    return result

  def _return_match_summaries(self):

    matches = Match.query().order(-Match.date)
    result = []

    for match in matches:
      tee = _get_tee_by_key(match.tee)
      result.append({
        'match_key': match.key.urlsafe(),
        'date': match.date.strftime('%Y-%m-%d'),
        'tee' : {
          'name': tee['name'],
          'slope': tee['slope'],
          'amcr': tee['amcr'],
          'par': tee['par'],
        }
      })

    return result



# Misc Functions
def _get_scores_for_member(member_key):
  score_query = Score.query(Score.member == member_key).order(Score.date)
  scores = []
  for score in score_query:
    scores.append({
      'date': score.date,
      'handicap': score.handicap,
      'scratch': score.scratch,
      'nett': score.nett,
      'tee': _get_tee_by_key(score.tee),
    })
  return scores


def _get_tee_by_key(tee_key):
  tee = tee_key.get()
  return {
    'name': tee.name,
    'course': tee.course,
    'slope': tee.slope,
    'amcr': tee.amcr,
    'par': tee.par,
  }

def _get_member_by_key(member_key):
  member = member_key.get()

  return {
    'first_name': member.first_name,
    'last_name': member.last_name,
  }

def _get_last_match_for_member(member_key):
  score = Score.query(Score.member == member_key).order(-Score.date).fetch(1)

  if score:
    return {
      'date': score[0].date.strftime('%Y-%m-%d'),
      'handicap': score[0].handicap,
      'scratch': score[0].scratch,
      'nett': score[0].nett,
      'points': score[0].points,
    }


app = webapp2.WSGIApplication([
  ('/api/add-club', AddClub),
  ('/api/list-clubs', ListClub),

  ('/api/add-members', AddMember),
  ('/api/list-members', ListMembers),

  ('/api/get-scores', GetScores),
  ('/api/delete-score', DeleteScore),

  ('/api/add-match', AddMatch),
  ('/api/get-match', GetMatch),
], debug=True)
