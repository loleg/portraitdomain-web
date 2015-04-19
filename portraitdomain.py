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

TAG_RE = re.compile(r'<[^>]+>')

def remove_tags(text):
    return TAG_RE.sub('', text)

def update(dbo):
    PD_PATH_META = "static/portraits-meta"
    PD_PATH_IMGS = "static/portraits-images"
    PD_PATH_ERRS = "static/portraits-errors"
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
        elems = [ desc.text for desc in sel(elem) ]
        if len(elems) == 0: continue
        desc = "".join(elems)
        shortname = getShortText(portraitname.decode('utf-8'), 16)

        # Write metadata
        textfilename = join(PD_PATH_IMGS, "%s.txt" % filename)
        if not isfile(textfilename):
            ftxt = open(textfilename, 'w')
            ftxt.write(remove_tags(desc).encode('utf8'))
            ftxt.close()

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
        
        if isfile(join(PD_PATH_ERRS, imagefile)):
            # If image was removed, mark it disabled
            dbo.update(
                { 'filename': filename },
                { '$set': { 'imagefile': '' }})

    # show contents of db
    return dbo.find().count()