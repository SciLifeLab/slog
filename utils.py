""" slog: Simple sample tracker system.

Utilities.

Per Kraulis
2011-02-04
"""

import time, datetime, uuid, hashlib, sys

# Import couchdb here to silence a strange warning message
# involving docutils and Python path change...
import couchdb
import docutils.core


DATE_ISO_FORMAT = "%Y-%m-%d"
TIME_ISO_FORMAT = "%H:%M:%S"

DATETIME_ISO_FORMAT = "%sT%sZ" % (DATE_ISO_FORMAT, TIME_ISO_FORMAT)


def url_id(id):
    "Return the absolute URL for the given entity id."

def now_iso():
    "Return current date-time in ISO format."
    return time.strftime(DATETIME_ISO_FORMAT, time.gmtime())

def id_uuid():
    "Return a random UUID for use as an identifier."
    return uuid.uuid4().hex

def hexdigest(value):
    return hashlib.md5(value).hexdigest()

def parse_iso_datetime(value):
    "Return the datetime object for the ISO format time string."
    try:
        ts = time.strptime(value, DATETIME_ISO_FORMAT)
    except ValueError:
        ts = time.strptime(value, DATE_ISO_FORMAT)
    return datetime.datetime.fromtimestamp(time.mktime(ts))

def get_login_account(dispatcher):
    "Get login account as default value for an Account Reference field."
    return dispatcher.user['name']

def rst_to_html(text, initial_header_level=2):
    "Convert reStructuredText to HTML."
    encoding = sys.getdefaultencoding()
    overrides = dict(input_encoding=encoding,
                     output_encoding=encoding,
                     initial_header_level=initial_header_level)
    result = docutils.core.publish_parts(source=text or '',
                                         writer_name='html',
                                         settings_overrides=overrides)
    return result['html_body']

def grid_coordinate(row=None, column=None, multiplex=None):
    """Return the string grid coordinate for the row/column/multiplex
    position values given as 0-based indexes."""
    parts = []
    if row is not None:
        if row >= 24:
            raise NotImplementedError
        parts.append(chr(ord('A')+row))
    if column is not None:
        parts.append(str(column+1))
    if multiplex is not None:
        parts.append(".%i" % (multiplex+1))
    return ''.join(parts)

def flatten(array):
    "Return the items in the hierarchical list of lists as a single list."
    result = []
    if isinstance(array, list):
        for item in array:
            result.extend(flatten(item))
    else:
        result.append(array)
    return result


if __name__ == '__main__':
    print flatten([[[1,2,3], [4,5], [None]],
                   ['q', 'w']])
