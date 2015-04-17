import string

def getShortText(text, limit=10):
    if text is None or text == "": return None
    if not isinstance(text, unicode): text = unicode(text)
    s = "".join([c for c in text 
        if c in string.letters 
        or c in string.digits 
        or c in string.whitespace])
    s = s.lower().replace(" ", "")
    return s[:limit]

def getIdentifier(name, werk):
    if name == "" or name is None: 
        return (None, None)
    name = getShortText(name, 11)
    werk = getShortText(werk, 5)
    if werk is None: werk = "_"
    return (name, werk)
