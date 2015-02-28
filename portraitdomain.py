from datetime import datetime
from os import listdir
from os.path import isfile, join
import re

def find_by_file(dbo, filename):
    """ Look up the id for a filename of image """
    rv = dbo.find_one({'filename': filename}, {'_id': 1})
    return rv['_id'] if rv else None

def update(dbo):
    PD_PATH_META = "static/portraits-meta"
    PD_PATH_IMGS = "static/portraits-images"
    pdfiles = [ f for f in listdir(PD_PATH_META) 
        if isfile(join(PD_PATH_META, f)) and not '.png' in f ]
    # load each file
    for f in pdfiles:
        filename = f.rstrip('.xml')
        # TODO: read metadata
        regexpname = re.compile(r"(.*)_-_.*")
        portraitname = regexpname.match(filename).group(1)
        # Convert image file
        imagefile = "%s.jpg" % (filename)
        if isfile(join(PD_PATH_IMGS, imagefile)):
            # skip if already in database
            if find_by_file(dbo, filename) is None:
                dbo.insert({
                    'name': portraitname,
                    'filename': filename,
                    'imagefile': imagefile,
                    'added': datetime.now(),
                    'user': None,
                    })
            else:
                dbo.update(
                    { 'filename': filename },
                    { '$set': {
                        'name': portraitname,
                        'imagefile': imagefile
                    }})
    # show contents of db
    return dbo.find().count()