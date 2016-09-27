"""

"""

from datetime import *
import json
import logging
import math
import urllib
import webapp2

from models import *
from operator import itemgetter

RESULT_NAMES = [
    'winner', 'runner_up', 'third_place', 'fourth_place', 'closest_pin_4th',
    'drive_chip_5th', 'drive_chip_6th', 'closest_pin_9th', 'closest_pin_10th',
    'closest_pin_16th', 'closest_pin_17th', 'longest_drive_0_18',
    'longest_drive_19plus', 'longest_drive_60over',
]

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
    club_future = club_key.get_async()
    club = club_future.get_result()
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
    adjust_score_for_win_str = self.request.get('adjust_score_for_win',
                                                default_value="True")
    show_inactive_str = self.request.get('show_inactive', default_value="True")

    adjust_score_for_win = adjust_score_for_win_str in ['True', '1', 'yes']
    show_inactive = show_inactive_str in ['True', '1', 'yes']

    @ndb.tasklet
    def callback(member):
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
        'match_wins': _get_total_wins_for_member(member.key),
        'handicap': _get_handicap_for_member(member.key, adjust_score_for_win),
      }
      if with_scores:
        member_data['scores'] = _get_scores_for_member(member.key)
      raise ndb.Return(member_data)

    query = Member.query()
    result = query.map(callback)

    self.response.content_type = 'application/json';
    self.response.out.write(json.dumps(result))


class GetMember(webapp2.RequestHandler):

  def get(self):
    member_key = self.request.get('member_key', default_value=None)
    key = ndb.Key(urlsafe=member_key)
    member_future = key.get_async()
    member = member_future.get_result()

    result = {
      'first_name': member.first_name,
      'last_name': member.last_name,
      'nick_name': member.nick_name,
      'email': member.email,
      'member_no': member.member_no,
      'phone_number1': member.phone_number1,
      'phone_number2': member.phone_number2,
      'initial_handicap': member.initial_handicap,
    }

    self.response.content_type = 'application/json';
    self.response.out.write(json.dumps(result))


# Score Management
class GetScores(webapp2.RequestHandler):
  """Retrieves all of the scores for a single member."""

  def get(self):
    member_key = self.request.get('member_key', default_value=None)
    adjust_score_for_win_str = self.request.get('adjust_score_for_win',
                                                default_value="True")

    adjust_score_for_win = adjust_score_for_win_str in ['True', '1', 'yes']

    key = ndb.Key(urlsafe=member_key)
    member_future = key.get_async()
    member = member_future.get_result()

    result = {
      'scores': _get_scores_for_member(member.key),
      'handicap': _get_handicap_for_member(member.key, adjust_score_for_win),
      'wins': _get_total_wins_for_member(member.key),
    }

    self.response.content_type = 'application/json';
    self.response.out.write(json.dumps(result))


class DeleteScore(webapp2.RequestHandler):
  """ """

  def get(self):
    pass


class UpdateScoreDates(webapp2.RequestHandler):


  def post(self):
    date = self.request.get('date')
    date_object = datetime.strptime(date, '%Y-%m-%d')
    match_date = date_object.date()

    score_key_values = self.request.get_all('score_keys')
    logging.debug('Score keys: %s', ','.join(score_key_values))
    # score_keys = [ndb.Key(urlsafe=key) for key in score_key_values]
    # scores = ndb.get_multi(score_keys)

    # for score in scores:
    #   score.date = match_date

    # ndb.put_multi(scores)


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

    if match_result['winner'] and match_result['winner'] != 'none':
      match.winner = ndb.Key(urlsafe=match_result['winner'])

    if match_result['runner_up'] and match_result['runner_up'] != 'none':
      match.runner_up = ndb.Key(urlsafe=match_result['runner_up'])

    if match_result['third_place'] and match_result['third_place'] != 'none':
      match.third_place = ndb.Key(urlsafe=match_result['third_place'])

    if match_result['fourth_place'] and match_result['fourth_place'] != 'none':
      match.fourth_place = ndb.Key(urlsafe=match_result['fourth_place'])

    if match_result['closest_pin_4th'] and match_result['closest_pin_4th'] != 'none':
      match.closest_pin_4th = ndb.Key(urlsafe=match_result['closest_pin_4th'])

    if match_result['drive_chip_5th'] and match_result['drive_chip_5th'] != 'none':
      match.drive_chip_5th = ndb.Key(urlsafe=match_result['drive_chip_5th'])

    if match_result['drive_chip_6th'] and match_result['drive_chip_6th'] != 'none':
      match.drive_chip_6th = ndb.Key(urlsafe=match_result['drive_chip_6th'])

    if match_result['closest_pin_9th'] and match_result['closest_pin_9th'] != 'none':
      match.closest_pin_9th = ndb.Key(urlsafe=match_result['closest_pin_9th'])

    if match_result['closest_pin_10th'] and match_result['closest_pin_10th'] != 'none':
      match.closest_pin_10th = ndb.Key(urlsafe=match_result['closest_pin_10th'])

    if match_result['closest_pin_16th'] and match_result['closest_pin_16th'] != 'none':
      match.closest_pin_16th = ndb.Key(urlsafe=match_result['closest_pin_16th'])

    if match_result['closest_pin_17th'] and match_result['closest_pin_17th'] != 'none':
      match.closest_pin_10th = ndb.Key(urlsafe=match_result['closest_pin_17th'])

    if match_result['longest_drive_0_18'] and match_result['longest_drive_0_18'] != 'none':
      match.longest_drive_0_18 = ndb.Key(urlsafe=match_result['longest_drive_0_18'])

    if match_result['longest_drive_19plus'] and match_result['longest_drive_19plus'] != 'none':
      match.longest_drive_19plus = ndb.Key(urlsafe=match_result['longest_drive_19plus'])

    if match_result['longest_drive_60over'] and match_result['longest_drive_60over'] != 'none':
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
        'date': score.date.strftime('%Y-%m-%d'),
        'key': score.key.urlsafe(),
      })

    result['scores'] = score_data

    prizes = []
    for name in RESULT_NAMES:
      prizes.append({
        'name': name,
        'winner': _get_member_by_key(getattr(match, name))
      })

    result['prizes'] = prizes

    return result

  def _return_match_summaries(self):

    @ndb.tasklet
    def callback(match):
      tee = _get_tee_by_key(match.tee)
      winner = _get_member_by_key(match.winner)
      raise ndb.Return({
        'match_key': match.key.urlsafe(),
        'date': match.date.strftime('%Y-%m-%d'),
        'tee' : {
          'name': tee['name'],
          'slope': tee['slope'],
          'amcr': tee['amcr'],
          'par': tee['par'],
        },
        'winner': _get_member_by_key(match.winner),
        'runner_up': _get_member_by_key(match.runner_up),
      })


    matches = Match.query().order(-Match.date)
    return matches.map(callback)


class DeleteMatch(webapp2.RequestHandler):

  def get(self):
    match_key = self.request.get('match_key')
    result = {'error': False}

    if match_key:
      try:
        self._do_match_delete(match_key)
      except:
        result = {'error': True}


    self.response.content_type = 'application/json';
    self.response.out.write(json.dumps(result))

  def _do_match_delete(self, match_key):
    key = ndb.Key(urlsafe=match_key)
    match = key.get()
    tee = _get_tee_by_key(match.tee)
    scores = ndb.get_multi(match.scores)

    keys = [s.key for s in scores]
    keys.append(key)
    self._tx_match_delete(keys)

  @ndb.transactional(xg=True)
  def _tx_match_delete(self, keys_list):
    ndb.delete_multi(keys_list)


# Misc Functions
def _get_scores_for_member(member_key):
  @ndb.tasklet
  def callback(score):
    raise ndb.Return({
      'date': score.date.strftime('%Y-%m-%d'),
      'handicap': score.handicap,
      'scratch': score.scratch,
      'nett': score.nett,
      'tee': _get_tee_by_key(score.tee),
    })
  score_query = Score.query(Score.member == member_key).order(Score.date)
  return score_query.map(callback)


@ndb.synctasklet
def _get_tee_by_key(tee_key):
  tee = yield tee_key.get_async()
  course = yield tee.course.get_async()
  club = yield course.club.get_async()

  raise ndb.Return({
    'name': tee.name,
    'course': {
      'name': course.name,
      'club': {
        'name': club.name,
      },
    },
    'slope': tee.slope,
    'amcr': tee.amcr,
    'par': tee.par,
  })

@ndb.synctasklet
def _get_member_by_key(member_key):
  member = None
  if member_key:
    member = yield member_key.get_async()

  if not member:
    logging.debug('Member was missing from database.')
    if member_key:
      logging.debug('Missing member key is %s.', member_key.urlsafe())

  raise ndb.Return({
    'first_name': member.first_name if member else '',
    'last_name': member.last_name if member else '',
  })


@ndb.synctasklet
def _get_last_match_for_member(member_key):

  @ndb.tasklet
  def callback(score):
    raise ndb.Return({
      'date': score.date.strftime('%Y-%m-%d'),
      'handicap': score.handicap,
      'scratch': score.scratch,
      'nett': score.nett,
      'points': score.points,
    })

  score = Score.query(Score.member == member_key).order(-Score.date)
  r = yield score.map_async(callback, limit=1)
  raise ndb.Return(r)


@ndb.synctasklet
def _get_total_wins_for_member(member_key):
  """How many times a member is marked as a 'winner'."""
  count = yield Match.query(Match.winner == member_key).count_async()
  raise ndb.Return(count)


def _get_handicap_for_member(member_key, adjust_score_for_win=True,
  load_all_scores=True):
  """Get the handicap for a member."""

  @ndb.tasklet
  def callback(score):
    tee = yield score.tee.get_async()
    win = yield Match.query(ndb.AND(Match.winner == member_key,
                              Match.date == score.date)).count_async()
    raise ndb.Return({
      'date': score.date.strftime('%Y-%m-%d'),
      'scratch': score.scratch,
      'nett': score.nett,
      'points': score.points,
      'par': tee.par,
      'slope': tee.slope,
      'amcr': tee.amcr,
      'win': win,
      'used_for_handicap': False,
    })

  member_future = member_key.get_async()
  scores = Score.query(Score.member == member_key)
  adj_scores_future = scores.map_async(callback)

  member = member_future.get_result()
  adj_scores = adj_scores_future.get_result()

  handicap = member.initial_handicap
  average = 0.0

  if adj_scores:
    adj_scores = sorted(_calculate_differetntial(adj_scores,
                                                adjust_score_for_win),
                        key=itemgetter('date'),
                        reverse=True)
    count = _get_scores_for_handicap(len(adj_scores))
    first_twenty = adj_scores[:20]
    the_rest = adj_scores[20:]
    first_twenty = sorted(first_twenty, key=itemgetter('differential'))

    total = 0.0;
    for i in xrange(count):
      total += first_twenty[i]['differential']
      first_twenty[i]['used_for_handicap'] = True

    average = math.floor((total / count) * 10) / 10
    handicap = round(average * 0.93, 1)

    adj_scores = first_twenty + the_rest
    adj_scores = sorted(adj_scores, key=itemgetter('date'))


  return {
    'handicap': handicap,
    'initial_handicap': member.initial_handicap,
    'scores': adj_scores,
    'average': average,
    'total_scores_used': _get_scores_for_handicap(len(adj_scores)),
  }


def _calculate_differetntial(scores, adjust_score_for_win=True):
  """Calculate the differential for a list of scores."""
  result = []
  for score in scores:
    if not score['slope']:
      score['slope'] = 113

    esc_adjustment = min(36, score['scratch'] - score['amcr'])
    if score['win'] and adjust_score_for_win:
      esc_adjustment = esc_adjustment - 2

    score['esc_adjustment'] = esc_adjustment

    differential = min((esc_adjustment * 113) / score['slope'], 36.4)
    score['differential'] = round(differential, 2)
    result.append(score)

  return result


def _get_scores_for_handicap(score_count):
  """ From http://www.golf.org.au/howtocalculateahandicap """
  if score_count < 7:
    return 1
  if score_count < 9:
    return 2
  if score_count < 11:
    return 3
  if score_count < 13:
    return 4
  if score_count < 15:
    return 5
  if score_count < 17:
    return 6
  if score_count < 19:
    return 7
  return 8

app = webapp2.WSGIApplication([
  ('/api/add-club', AddClub),
  ('/api/list-clubs', ListClub),

  ('/api/add-members', AddMember),
  ('/api/list-members', ListMembers),
  ('/api/get-member', GetMember),

  ('/api/get-scores', GetScores),
  ('/api/delete-score', DeleteScore),
  ('/api/update-score-dates', UpdateScoreDates),

  ('/api/add-match', AddMatch),
  ('/api/get-match', GetMatch),
  ('/api/delete-match', DeleteMatch),
], debug=True)
