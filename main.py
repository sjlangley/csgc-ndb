

import hashlib
import json
import urllib.request

from datetime import date
from flask import Flask, render_template, request, url_for
from pymemcache.client.base import Client
from operator import itemgetter

def sha1(msg: str) -> str:
    return hashlib.sha1(msg.encode()).hexdigest()

class JsonSerde(object):
    def serialize(self, key, value):
        if isinstance(value, str):
            return value.encode('utf-8'), 1
        return json.dumps(value).encode('utf-8'), 2

    def deserialize(self, key, value, flags):
       if flags == 1:
           return value.decode('utf-8')
       if flags == 2:
           return json.loads(value.decode('utf-8'))
       raise Exception("Unknown serialization format")
    
client = Client('192.168.1.5', serde=JsonSerde())

def __retrieve_data(url: str):
    key = sha1(url)


    data = client.get(key)
    if data:
        app.logger.debug("Key %s found in cache." % url)
        return data


    with urllib.request.urlopen("http://csocgolf.appspot.com/" + url, timeout=120) as response:
        html = response.read()
        data = json.loads(html)
        client.set(key, data, expire=3600)
        return data



app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    template_values = _get_standard_template_properties(request)
    return render_template("index.html", **template_values)


@app.route('/list_members_general')
def list_members_general():

    data = __retrieve_data("api/list-members")

    # Determine sorting
    sort_order = request.args.get('sort_by', 'member_no')
    sort_direction = request.args.get('sort_direction', 'asc')
    reverse = sort_direction == 'desc'
    member_data = sorted(data, key=itemgetter(sort_order), reverse=reverse)

    template_values = _get_standard_template_properties(request)
    template_values['member_list'] = member_data
    template_values['daily_slope_rating'] = 118 / float(113)
        
    return render_template("list_members.html", **template_values)


@app.route('/show-latest-result')
def show_latest_result():
    pass


@app.route('/login-url')
def login_url():
    pass


@app.route('/list-club-general')
def list_club_general():

    template_values = _get_standard_template_properties(request)
    template_values['club_data'] = __retrieve_data("api/list-clubs")
    return render_template("list_clubs.html", **template_values)


@app.route('/show-match-result')
def show_match_result():
    """ Can show a detailed result, or a partial result. """


    def _show_brief_match_result():
            template_values = _get_standard_template_properties(request)
            template_values['matches'] = __retrieve_data("api/get-match")
            return render_template("brief_match_results.html", **template_values)


    def __show_detailed_match_report(match_ker: str):
            match_data = __retrieve_data("api/get-match?match_key=" + match_key)
            scores = sorted(match_data['scores'], key=itemgetter('points'), reverse=True)

            template_values = _get_standard_template_properties(request)
            template_values['matches'] = match_data
            template_values["scores"] = scores
            template_values['prizes'] = match_data['prizes']
            return render_template("detailed_match_results.html", **template_values)


    match_key = request.args.get('match_key')

    if match_key:
        return __show_detailed_match_report(match_key)
    else:
        return _show_brief_match_result()      


@app.route('/show-member-details')
def show_member_details():
    """ Prints all data about a specific member."""
    member_key = request.args.get('member_key')

    url = 'api/get-scores?member_key=' + member_key
    data = __retrieve_data(url)

    score_data = []
    for score, hc_data in zip(data['scores'], data['handicap']['scores']):
      score_data.append({
        'date': score['date'],
        'scratch':  score['scratch'],
        'nett': score['nett'],
        'handicap': score['handicap'],
        'tee': score['tee'],
        'slope': hc_data['slope'],
        'amcr': hc_data['amcr'],
        'differential': hc_data['differential'],
        'win': hc_data['win'],
        'used': hc_data['used_for_handicap'],
      })

    score_data = sorted(score_data, key=itemgetter("date"), reverse=True)

    template_values = _get_standard_template_properties(request)
    template_values['score_data'] = score_data
    template_values['hc_data'] = data['handicap']
    template_values['wins'] = data['wins']
    template_values['member_data'] = data
    template_values['handicap_multiplier'] = '0.93'    

    return render_template("show_member_details.html", **template_values)


@app.route('/add-members-url')
def add_members_url():
    pass

@app.route('/add-club-url')
def add_club_url():
    pass

@app.route('/add-match-result-url')
def add_match_result_url():
    
    def __phase_1():
        data = __retrieve_data("api/list-clubs")
        clubs = [{'name': club['name'], 'key': club['key']} for club in data]
        template_values = _get_standard_template_properties(request)
        template_values['clubs'] = clubs

        return render_template("add_match_result_phase_1.html", **template_values)

    def __phase_2():
        
        member_data = __retrieve_data("api/list-members-without-statistics")

        club_key = request.args.get('club_key', None)
        club_data = __retrieve_data("api/list-clubs?club_key=" + club_key)

        template_values = _get_standard_template_properties(request)
        template_values['member_data'] = sorted(member_data, key=itemgetter('last_name'))
        template_values['club_name'] = club_data[0]['name']
        template_values['course_data'] = club_data[0]['courses']
        template_values['max_player_results'] = 26
        template_values['submit_score_url'] = 'https://csocgolf.appspot.com/api/add-match'
        template_values['todays_date'] = date.today().strftime('%Y-%m-%d')

        return render_template("add_match_result_phase_2.html", **template_values)

    phase = request.args.get('phase')

    if not phase:
        return __phase_1()
    else:
        return __phase_2()

@app.route('/list-member-admin-url')
def list_member_admin_url():
    pass

def _get_standard_template_properties(request_data):
    template_values = {
        'admin_user': True,
    }

    return template_values


if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)