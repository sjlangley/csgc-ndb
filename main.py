"""

"""
import os

from google.appengine.api import urlfetch
from google.appengine.api import users

from datetime import date
import json
import jinja2
from operator import itemgetter
from urlparse import urlparse
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader([
    os.path.dirname(__file__),
    os.path.dirname(__file__) + '/templates',
  ]),
  extensions=['jinja2.ext.autoescape'],
  autoescape=True)

class MainPage(webapp2.RequestHandler):
  """   """

  def get(self):
    """   """
    template_values = _get_standard_template_properties(self.request)

    template = JINJA_ENVIRONMENT.get_template('main.html')
    self.response.write(template.render(template_values))


class AddMembers(webapp2.RequestHandler):
  """Add new members to the club."""

  def get(self):
    url = '%s/api/add-members' % self.request.host_url

    template_values = _get_standard_template_properties(self.request)
    template_values['add_member_post_url'] = url
    template_values['form_size'] = 10

    template = JINJA_ENVIRONMENT.get_template('add_members.html')
    self.response.write(template.render(template_values))


class AddClub(webapp2.RequestHandler):
  """Add a new club."""

  def get(self):
    url = '%s/api/add-club' % self.request.host_url

    template_values = _get_standard_template_properties(self.request)
    template_values['add_club_post_url'] = url
    template_values['courses_per_club'] = 2
    template_values['tees_per_course'] = 3

    template = JINJA_ENVIRONMENT.get_template('add_club.html')
    self.response.write(template.render(template_values))


class ListClubGeneral(webapp2.RequestHandler):
  """List Club Details."""

  def get(self):

    url = "%s/api/list-clubs" % self.request.host_url

    club_key = self.request.get('club-key', allow_multiple=True)
    result = urlfetch.fetch(url, follow_redirects=True)
    data = json.loads(result.content)

    template_values = _get_standard_template_properties(self.request)
    template_values['club_data'] = data

    template = JINJA_ENVIRONMENT.get_template('list_clubs.html')
    self.response.write(template.render(template_values))


class ListMembersGeneral(webapp2.RequestHandler):
  """List Current Members Basic Info."""

  def get(self):

    url = '%s/api/list-members' % self.request.host_url
    result = urlfetch.fetch(url, follow_redirects=False)
    data = json.loads(result.content)

    template_values = _get_standard_template_properties(self.request)
    template_values['member_list'] = data
    template_values['show_pii'] = False

    template = JINJA_ENVIRONMENT.get_template('list_members.html')
    self.response.write(template.render(template_values))


class ListMembers(webapp2.RequestHandler):
  """List Current Members with PII information."""

  def get(self):
    url = '%s/api/list-members' % self.request.host_url
    result = urlfetch.fetch(url, follow_redirects=False)
    data = json.loads(result.content)

    template_values = _get_standard_template_properties(self.request)
    template_values['member_list'] = data
    template_values['show_pii'] = True

    template = JINJA_ENVIRONMENT.get_template('list_members.html')
    self.response.write(template.render(template_values))


class AddMatchResult(webapp2.RequestHandler):
  """Adds a new result of a match."""

  def get(self):
    phase = self.request.get('phase')

    if not phase:
      self._phase_1()
    else:
      self._phase_2()


  def _phase_1(self):
    """User wants to select the Club the Game was played at."""

    url = "%s/api/list-clubs" % self.request.host_url
    result = urlfetch.fetch(url, follow_redirects=False)
    data = json.loads(result.content)

    clubs = [{'name': club['name'], 'key': club['key']} for club in data]
    template_values = _get_standard_template_properties(self.request)
    template_values['clubs'] = clubs

    template = JINJA_ENVIRONMENT.get_template('add_match_result_phase_1.html')
    self.response.write(template.render(template_values))

  def _phase_2(self):
    """We know the club, input the results."""
    members_url = '%s/api/list-members' % self.request.host_url
    result = urlfetch.fetch(members_url, follow_redirects=False)
    member_data = json.loads(result.content)

    club_key = self.request.get('club_key', None)
    club_url = '%s/api/list-clubs?club_key=%s' % (self.request.host_url, club_key)
    result = urlfetch.fetch(club_url, follow_redirects=False)
    club_data = json.loads(result.content)

    template_values = _get_standard_template_properties(self.request)
    template_values['member_data'] = member_data
    template_values['club_name'] = club_data[0]['name']
    template_values['course_data'] = club_data[0]['courses']
    template_values['max_player_results'] = 26
    template_values['submit_score_url'] = '%s/api/add-match' % self.request.host_url
    template_values['todays_date'] = date.today().strftime('%Y-%m-%d')
    template = JINJA_ENVIRONMENT.get_template('add_match_result_phase_2.html')
    self.response.write(template.render(template_values))


class ShowMatchResult(webapp2.RequestHandler):

  def get(self):
    match_key = self.request.get('match_key')

    if match_key:
      self._show_detailed_match_results(match_key)
    else:
      self._show_brief_match_results()

  def _show_detailed_match_results(self, match_key):
    """Show full details about one match."""
    url = '%s/api/get-match?match_key=%s' % (self.request.host_url, match_key)
    result = urlfetch.fetch(url, follow_redirects=False)
    match_data = json.loads(result.content)

    template_values = _get_standard_template_properties(self.request)
    template_values['match'] = match_data
    template_values['scores'] = sorted(match_data['scores'], key=itemgetter('points'), reverse=True)
    template = JINJA_ENVIRONMENT.get_template('detailed_match_results.html')
    self.response.write(template.render(template_values))

  def _show_brief_match_results(self):
    pass

class ShowFailure(webapp2.RequestHandler):
  """Show a generic failure message."""

  def get(self):
    template_values = _get_standard_template_properties(self.request)
    template_values['heading'] = self.request.get('heading')
    template_values['message'] = self.request.get('message')

    template = JINJA_ENVIRONMENT.get_template('failure.html')
    self.response.write(template.render(template_values))


def _get_standard_template_properties(request):
  """Return a dictionary of the standard template values."""
  if users.get_current_user():
    url = users.create_logout_url(request.uri)
    url_linktext = 'Logout'
  else:
    url = users.create_login_url(request.uri)
    url_linktext = 'Login'

  parse_result = urlparse(request.path_url)

  base =  '%s://%s' % (parse_result.scheme, parse_result.netloc)

  template_values = {
    # Top Navbar Links
    'home_url': base,
    'login_url': url,
    'login_url_linktext': url_linktext,
    # General Links
    'list_members_general': '%s/list-members-general' % base,
    'list_club_general': '%s/list-club-general' % base,
    'show_match_result': '%s/show-match-result' % base,

    # Admin Links
    'add_club_url': '%s/add-club' % base,
    'add_members_url': '%s/add-members' % base,
    'list_member_admin_url': '%s/list-members-admin' % base,
    'add_match_result_url': '%s/add-match-result' % base,
    'admin_user': True,
  }

  return template_values


app = webapp2.WSGIApplication([
  ('/', MainPage),
  # Club Functions
  ('/list-members-general', ListMembersGeneral),
  ('/list-club-general', ListClubGeneral),
  ('/show-match-result', ShowMatchResult),

  # Admin Functions
  ('/add-club', AddClub),
  ('/add-members', AddMembers),
  ('/add-match-result', AddMatchResult),
  ('/list-members-admin', ListMembers),

  # Generic Help/Error Pages
  ('/failure', ShowFailure),
], debug=True)
