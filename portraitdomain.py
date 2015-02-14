from datetime import datetime
from os import listdir
from os.path import isfile, join

def find_by_file(dbo, filename):
    """ Look up the id for a filename of image """
    rv = dbo.find_one({'filename': filename}, {'_id': 1})
    return rv['_id'] if rv else None

def update(dbo):
    PD_PATH_META = "portraits-meta"
    PD_PATH_IMGS = "static/portraits"
    pdfiles = [ f for f in listdir(PD_PATH_META) 
        if isfile(join(PD_PATH_META, f)) ]
    # load each file
    for f in pdfiles:
        filename = f.rstrip('.xml')
        # TODO read metadata
        imagefile = "%s.jpg" % (filename)
        if isfile(join(PD_PATH_IMGS, imagefile)):
            # skip if already in database
            if find_by_file(dbo, filename) is None:
                dbo.insert({
                    'filename': filename,
                    'imagefile': imagefile,
                    'added': datetime.now(),
                    'user': None,
                    })
    # show contents of db
    return dbo.find().count()