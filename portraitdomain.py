from datetime import datetime
from os import listdir
from os.path import isfile, join
from lxml import etree
from lxml.cssselect import CSSSelector
from io import StringIO, BytesIO
import re
from identifier import getShortText

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

        # Get name from filename
        regexpname = re.compile(r"(.*)_-_.*_-_.*")
        portraitname = regexpname.match(filename).group(1)
        portraitname = portraitname.replace('_', ' ')

        # Read metadata
        tree = etree.parse(join(PD_PATH_META, f))
        elem = tree.getroot()
        sel = CSSSelector('response description language')
        elems = [ desc for desc in sel(elem) ]
        if len(elems) == 0: continue
        desc = elems[0].text
        shortname = getShortText(portraitname.decode('utf-8'), 16)

        imagefile = "%s.jpg" % (filename)
        if isfile(join(PD_PATH_IMGS, imagefile)):
            # Update entry in database
            if find_by_file(dbo, filename) is None:
                dbo.insert({
                    'name': portraitname,
                    'shortname': shortname,
                    'description': desc,
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
                        'shortname': shortname,
                        'description': desc,
                        'imagefile': imagefile
                    }})
    # show contents of db
    return dbo.find().count()