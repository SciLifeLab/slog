""" slog: Simple sample tracker system.

Load the system account into the database. Required at db creation.

Per Kraulis
2011-02-22
"""

from slog import utils
from slog.load import put_document


ACCOUNTS = {'admin': dict(entity='account',
                          name='system',
                          role='admin',
                          password=utils.hexdigest('rubb1sh'),
                          fullname='System administrator',
                          timestamp=utils.now_iso())}

if __name__ == '__main__':
    map(put_document, ACCOUNTS.values())
