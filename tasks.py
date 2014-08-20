"""
"""

from google.appengine.api import taskqueue
from google.appengine.api import urlfetch

import json
import logging
import webapp2

class FixScoreDates(webapp2.RequestHandler):

  def get(self):
    match_key = self.request.get('match_key')

    if match_key:
      self._fix_score_dates(match_key)
    else:
      self._enqueue_fix_score_tasks()



  def _enqueue_fix_score_tasks(self):
    url = '%s/api/get-match' % self.request.host_url
    result = urlfetch.fetch(url, follow_redirects=False, deadline=30)
    match_data = json.loads(result.content)

    for match in match_data:
      taskqueue.add(url='/tasks/fix-score-dates',
                    params = {'match_key': match['match_key']},
                    method = 'GET')


  def _fix_score_dates(self, match_key):
    url = '%s/api/get-match?match_key=%s' % (self.request.host_url, match_key)
    result = urlfetch.fetch(url, follow_redirects=False, deadline=30)
    match_data = json.loads(result.content)

    mismatch_dates = [score['key'] for score in match_data['scores'] if score['date'] != match_data['date']]

    if mismatch_dates:
      logging.debug('Found a mismatched date')




app = webapp2.WSGIApplication([
  ('/tasks/fix-score-dates', FixScoreDates),
], debug=True)
