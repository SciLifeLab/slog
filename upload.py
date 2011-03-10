""" slog: Simple sample tracker system.

Upload a file attachment to an entity in the slog database.

Load the XML and PNG files for an Illumina machine run.

Per Kraulis
2011-02-28
"""

import os, httplib, urlparse, base64, mimetypes


class Uploader(object):
    "Upload a file attachment to an entity in the slog database."

    BOUNDARY = '----------$$this_is_the_multipart_boundary$$'

    def __init__(self, url_base, user, password):
        "Set the URL base for the slog system, and the account to use."
        self.url_base = url_base.rstrip('/') # Must not have trailing slash
        self.user = user
        self.password = password
        self.headers = dict()

    def post(self, entity, filename, content=None):
        """Upload a file as an attachment to the given entity.
        The entity is specified as {entitytype}/{entityname}.
        If 'content' is None, then read the content from the given named file.
        This uses HTTP POST, encoding the content as multipart form data.
        Return the HTTP response string 'status reason'."""
        key = '_attachment'
        if content is None:
            content = open(filename).read()
        filename = os.path.basename(filename)
        data = self.encode_multipart_formdata(files=[(key, filename, content)])
        self.set_authorization()
        self.headers['Content-Type'] = "multipart/form-data; boundary=%s" % self.BOUNDARY
        return self.get_response('POST', "%s/%s" % (self.url_base,entity), data)

    def put(self, docid, filename, content=None):
        """Upload a file as an attachment to the given document.
        The document is specified by its id.
        If 'content' is None, then read the content from the given named file.
        This uses HTTP PUT, sending the data without any encoding.
        Return the HTTP response string 'status reason'."""
        self.set_authorization()
        if content is None:
            content = open(filename).read()
        filename = os.path.basename(filename)
        return self.get_response('PUT', 
                                 "%s/attachment/%s/%s" % (self.url_base,
                                                          docid,
                                                          filename),
                                 content)

    def get_response(self, command, url, data):
        "Send the HTTP request and return the HTTP response string."
        url = urlparse.urlsplit(url)
        http = httplib.HTTPConnection(url.netloc)
        http.request(command, url.path, data, self.headers)
        response = http.getresponse()
        return "%s %s" % (response.status, response.reason)

    def set_authorization(self):
        "Set the 'Authorization' header item."
        credentials = base64.b64encode("%s:%s" % (self.user, self.password))
        self.headers['Authorization'] = "Basic %s" % credentials

    def encode_multipart_formdata(self, fields=[], files=[]):
        """Return the form data encoded as 'multipart/form-data'.
        'fields' is a sequence of (name, value) tuples for regular form fields.
        'files' is a sequence of either filepaths (which will be opened and
        read), already opened 'file' objects (from which filename and data
        will be read) or tuples (key, filename, value), to be encoded
        as 'multipart/form-data'.
        This is modified from code written by Wade Leftwich, found at
        http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/146306"""
        result = []
        for (key, value) in fields:
            result.append('--' + self.BOUNDARY)
            result.append('Content-Disposition: form-data; name="%s"' % key)
            result.append('')
            result.append(value)
        for fileitem in files:
            if isinstance(fileitem, basestring):
                filename = os.path.basename(fileitem)
                value = open(fileitem).read()
                key = 'file'
            elif isinstance(fileitem, tuple):
                (key, filename, value) = fileitem
            else:
                try:
                    filename = fileitem.name
                    value = fileitem.read()
                    key = 'file'
                except AttributeError:
                    raise TypeError("invalid fileitem '%s'" % fileitem)
            result.append('--' + self.BOUNDARY)
            result.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            t = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            result.append("Content-Type: %s" % t)
            result.append('Content-Transfer-Encoding: base64')
            result.append('')
            value = base64.standard_b64encode(value)
            result.append(value)
        result.append('--' + self.BOUNDARY + '--')
        result.append('')
        return '\r\n'.join(result)


# XXX change to upload to task!
## def load_instrumentrun():
##     "Load the XML and PNG files for an Illumina machine run."
##     name = '101214_sN188_0159_B80NPTAXX'
##     uploader = Uploader('http://localhost/slog', 'cbg', 'cbg123')
##     for filename in ['data/QScore_L1.png',
##                      'data/QScore_L2.png',
##                      'data/QScore_L3.png',
##                      'data/QScore_L4.png',
##                      'data/QScore_L5.png',
##                      'data/QScore_L6.png',
##                      'data/QScore_L7.png',
##                      'data/QScore_L8.png',
##                      'data/NumGT30_L1.png',
##                      'data/NumGT30_L2.png',
##                      'data/NumGT30_L3.png',
##                      'data/NumGT30_L4.png',
##                      'data/NumGT30_L5.png',
##                      'data/NumGT30_L6.png',
##                      'data/NumGT30_L7.png',
##                      'data/NumGT30_L8.png',
##                      'data/ErrRate_L1.png',
##                      'data/ErrRate_L2.png',
##                      'data/ErrRate_L3.png',
##                      'data/ErrRate_L4.png',
##                      'data/ErrRate_L5.png',
##                      'data/ErrRate_L6.png',
##                      'data/ErrRate_L7.png',
##                      'data/ErrRate_L8.png'
##         ]:
##         print uploader.post("instrumentrun/%s" % name, filename)
##         print filename, uploader.put('465d33ea851b4935a6255e4008287202', filename)

## if __name__ == '__main__':
##     load_instrumentrun()
