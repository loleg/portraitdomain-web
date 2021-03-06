# -*- coding: utf-8 -*-
from datetime import datetime
from hashlib import md5

import pytz
from flask import Flask, request, session, url_for, redirect, \
    render_template, abort, g, flash
from werkzeug.security import check_password_hash, generate_password_hash
from flask.ext.pymongo import PyMongo
from bson.objectid import ObjectId
from random import shuffle

import portraitdomain

import logging

# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DEBUG=True,
    SECRET_KEY='development key'))
app.config.from_envvar('MINITWIT_SETTINGS', silent=True)
app.config.from_object('config')

# setup mongodb
mongo = PyMongo(app)

# divert logging
print "Logging to %s" % app.config['LOG_FILE']
logging.basicConfig(filename=app.config['LOG_FILE'], level=logging.INFO, format='%(asctime)s %(message)s')

def get_user_id(username):
    """Convenience method to look up the id for a username."""
    rv = mongo.db.user.find_one({'username': username}, {'_id': 1})
    return rv['_id'] if rv else None


def format_datetime(timestamp):
    """Format a timestamp for display."""
    return timestamp.replace(tzinfo=pytz.utc).strftime('%Y-%m-%d @ %H:%M')


def gravatar_url(email, size=80):
    """Return the gravatar image for the given email address."""
    return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
           (md5(email.strip().lower().encode('utf-8')).hexdigest(), size)


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = mongo.db.user.find_one({'_id': ObjectId(session['user_id'])})


@app.route('/')
def timeline():
    """Shows a users timeline or if no user is logged in it will
    redirect to the public timeline.  This timeline shows the user's
    messages as well as all the messages of followed users.
    """
    if not g.user:
        return redirect(url_for('public_timeline'))
    return redirect(url_for('user_timeline', username=g.user['username']))

@app.route('/public')
def public_timeline():
    """Displays the latest messages of all users."""
    past = request.args.get('past')
    if past is None:
        messages = mongo.db.message.find().sort('pub_date', -1).limit(10)
    else:
        past = datetime.strptime(past.split('.')[0], "%Y-%m-%d %H:%M:%S")
        messages = mongo.db.message.find({ 'pub_date': { '$lt': past } }).sort('pub_date', -1).limit(10)
    return render_template('timeline.html', messages=messages)

@app.route('/search')
def search_result():
    """Searches user and post data"""
    query = request.args.get('q')
    if len(query) < 3:
        flash('Search query too short to be of much use ...')
        return redirect(url_for('public_timeline'))
    regex = ".*%s.*" % query
    messages = mongo.db.message.find({
        "text": { "$regex": query, "$options":"i" }
    }).sort('pub_date', -1)
    portraits = mongo.db.portrait.find({
        "name": { "$regex": query, "$options":"i" }
    }).sort('name', 1)
    return render_template(
        'timeline.html', 
        messages=messages, 
        portraits=portraits,
        query=query
    )

@app.route('/go/<shortname>')
def go_link(shortname):
    """ Expands shortlink to portrait """
    p = mongo.db.portrait.find_one({
        'shortname': shortname })
    if p is None:
        logging.error("'%s' shortlink not resolved" % shortname)
        abort(404)
    pid = p['_id']
    logging.info("'%s' was shortlinked from '%s'" % (p['name'], shortname))
    return redirect(url_for('face_timeline', pid=pid))

@app.route('/<username>')
def user_timeline(username):
    """Display's a users tweets."""
    profile_user = mongo.db.user.find_one({
        'username': username })
    if profile_user is None:
        abort(404)
    # Work out followers
    followed = False
    if g.user:
        followed = mongo.db.follower.find_one(
            {'who_id': ObjectId(session['user_id']),
             'whom_id': {'$in': [ObjectId(profile_user['_id'])]}}) is not None
    # Get messages
    messages = mongo.db.message.find(
        {'author_id': ObjectId(profile_user['_id'])}).sort('pub_date', -1)
    # Get portrait if selected
    portrait = None
    if 'portrait_id' in profile_user:
        portrait = mongo.db.portrait.find_one(
            {'_id': ObjectId(profile_user['portrait_id'])})
        logging.info("'%s' was profiled as user (%s)" % (portrait['name'], username))
    return render_template('timeline.html', messages=messages,
        followed=followed, profile_user=profile_user,
        portrait=portrait)

@app.route('/face/<pid>')
def face_timeline(pid):
    """Displays tweets by portrait."""
    profile_user = mongo.db.user.find_one({'portrait_id': pid})
    # Get messages
    messages = mongo.db.message.find(
        {'portrait_id': pid}).sort('pub_date', -1)
    # Get portrait
    portrait = mongo.db.portrait.find_one(
        {'_id': ObjectId(pid)})
    logging.info("'%s' was profiled" % portrait['name'])
    return render_template('timeline.html', messages=messages,
        profile_user=profile_user,
        portrait=portrait)

@app.route('/<username>/follow')
def follow_user(username):
    """Adds the current user as follower of the given user."""
    if not g.user:
        abort(401)
    whom_id = get_user_id(username)
    if whom_id is None:
        abort(404)
    mongo.db.follower.update(
        {'who_id': ObjectId(session['user_id'])},
        {'$push': {'whom_id': whom_id}}, upsert=True)
    flash('You are now following "%s"' % username)
    return redirect(url_for('user_timeline', username=username))

@app.route('/<username>/unfollow')
def unfollow_user(username):
    """Removes the current user as follower of the given user."""
    if not g.user:
        abort(401)
    whom_id = get_user_id(username)
    if whom_id is None:
        abort(404)
    mongo.db.follower.update(
        {'who_id': ObjectId(session['user_id'])},
        {'$pull': {'whom_id': whom_id}})
    flash('You are no longer following "%s"' % username)
    return redirect(url_for('user_timeline', username=username))


@app.route('/add_message', methods=['POST'])
def add_message():
    """Registers a new message for the user."""
    if 'user_id' not in session:
        abort(401)
    if request.form['text']:
        user = mongo.db.user.find_one(
            {'_id': ObjectId(session['user_id'])})
        pid = None
        pname = ""
        pfile = ""
        if 'portrait_file' in user:
            pid = user['portrait_id']
            pname = user['portrait_name']
            pfile = user['portrait_file']
        mongo.db.message.insert(
            {'author_id': ObjectId(session['user_id']),
             'email': user['email'],
             'username': user['username'],
             'text': request.form['text'],
             'pub_date': datetime.utcnow(),
             'portrait_id': pid,
             'portrait_file': pfile,
             'portrait_name': pname
            })
        flash('Your message was recorded')
        logging.info("(%s) posted as '%s'" % (user['username'], user['portrait_name']))
    return redirect(url_for('timeline'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in."""
    if g.user:
        return redirect(url_for('timeline'))
    error = None
    if request.method == 'POST':
        user = mongo.db.user.find_one({'username': request.form['username']})
        if user is None:
            error = 'Invalid username'
            logging.error('Attempted log in with invalid username')
        elif not check_password_hash(user['pw_hash'], request.form['password']):
            error = 'Invalid password'
            logging.error('Attempted log in with invalid password')
        else:
            flash('You were logged in')
            session['user_id'] = str(user['_id'])
            logging.info("(%s) has logged in" % user['username'])
            return redirect(url_for('timeline'))
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers the user."""
    if g.user:
        return redirect(url_for('timeline'))
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['email'] or '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
        elif get_user_id(request.form['username']) is not None:
            error = 'The username is already taken'
        else:
            mongo.db.user.insert(
                {'username': request.form['username'],
                 'email': request.form['email'],
                 'pw_hash': generate_password_hash(request.form['password'])})
            flash('You were successfully registered and can login now')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('public_timeline'))

@app.route('/portraits/update')
def portraits_update():
    """ Reloads portraits database """
    count = portraitdomain.update(mongo.db.portrait)
    return "Count: %d" % count

@app.route('/portraits/get/<userid>')
def portraits_get(userid):
    """ Fetches filename of portrait for user """
    user = mongo.db.user.find_one(
        {'_id': ObjectId(userid)})
    if user is None:
        abort(404)
    if 'portrait_file' in user:
        pfile = user['portrait_file']
        return redirect('/static/portraits-images/%s' % pfile)
    else:
        pfile = "default.png"
        return redirect('/static/res/%s' % pfile)

@app.route('/portraits/select/<pid>')
def portraits_select(pid):
    """ Assign portrait to user """
    if 'user_id' not in session:
        flash('Please login or register, then go back to adopt the portrait.')
        return redirect('/login')
    portrait = mongo.db.portrait.find_one(
        {'_id': ObjectId(pid)})
    if portrait is None:
        abort(404)
    # Unselect previous portrait
    user = mongo.db.user.find_one(
        {'_id': ObjectId(session['user_id'])})
    if 'portrait_id' in user:
        mongo.db.portrait.update(
            { '_id': ObjectId(user['portrait_id']) },
            { '$set': {
                'user': None
            }})
    # Update portrait
    mongo.db.portrait.update(
        { '_id': ObjectId(pid) },
        { '$set': {
            'user': session['user_id']
        }})
    # Update user
    mongo.db.user.update(
        { '_id': ObjectId(session['user_id']) },
        { '$set': {
            'portrait_id': pid,
            'portrait_file': portrait['imagefile'],
            'portrait_name': portrait['name']
        }})
    logging.info("'%s' was adopted" % portrait['name'])
    flash('Your identity has been changed: you are now %s' % portrait['name'])
    return redirect(url_for('user_timeline', username=user['username']))

@app.route('/portraits')
def portraits():
    """ Browse the portraits """
    if 'user_id' not in session:
        abort(401)
        # Todo: check g.user for selected portrait
    portraits = list(mongo.db.portrait.find(
            {'user': None, 'imagefile': { '$ne': '' }}
        ).limit(300))
    shuffle(portraits)
    return render_template('portraits.html', portraits=portraits[:21])

@app.route('/about')
def about_page():
    """ Some information aboot this project """
    return render_template('about.html')

# add some filters to jinja
app.jinja_env.filters['datetimeformat'] = format_datetime
app.jinja_env.filters['gravatar'] = gravatar_url

if __name__ == '__main__':
    app.run(port=1852)
