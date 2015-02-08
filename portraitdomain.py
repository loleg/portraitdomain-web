from os import listdir
from os.path import isfile, join

from flask import current_app, Blueprint, render_template, abort
from jinja2 import TemplateNotFound

from flask.ext.pymongo import PyMongo

from minitwit import mongo

portraitdomain = Blueprint('portraitdomain', __name__,
    template_folder='templates')

def find_by_file(filename):
    """ Look up the id for a filename of image """
    rv = mongo.db.user.find_one({'filename': filename}, {'_id': 1})
    return rv['_id'] if rv else None

@portraitdomain.route('/update')
def update():
    """ Reloads portraits database """
    PD_PATH_META = "data/meta"
    PD_PATH_IMGS = "data/images"
    pdfiles = [ f for f in listdir(PD_PATH_META) 
        if isfile(join(PD_PATH_META, f)) ]
    # load each file
    for f in pdfiles:
        filename = f.rstrip('.xml')
        imagefile = "%s.jpg" % (filename)
        if isfile(join(PD_PATH_IMGS, imagefile)):
            # skip if already in database
            if not find_by_file(filename):
                mongo.db.portrait.insert({
                    'filename': filename,
                    'imagefile': imagefile,
                    'added': pytz.utc,
                    'user': None,
                    })
    # show contents of db
    portraits = mongo.db.portrait.find()
    return len(portraits)
