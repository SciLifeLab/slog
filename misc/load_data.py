""" slog: Simple sample tracker system.

Load some initial data documents into the database.

Per Kraulis
2011-02-01
2011-02-14  modified document design
"""

from slog import utils
from slog.load import put_document


ACCOUNTS = {'admin': dict(entity='account',
                          name='system',
                          role='admin',
                          password=utils.hexdigest('rubb1sh'),
                          fullname='System administrator',
                          timestamp=utils.now_iso()),
            'max_kaller': dict(entity='account',
                               name='max_kaller',
                               role='manager',
                               password=utils.hexdigest('flax'),
                               fullname='Kaller, Max',
                               timestamp=utils.now_iso()),
            'joakim_lundeberg': dict(entity='account',
                                     name='joakim_lundeberg',
                                     role='customer',
                                     password=utils.hexdigest('jocke'),
                                     fullname='Lundeberg, Joakim',
                                     timestamp=utils.now_iso())}

PROJECTS = [dict(entity='project',
                 name='J_Johansson_10_01',
                 title='Spruce genome',
                 customer='joakim_lundeberg',
                 status='defined',
                 timestamp='2011-02-01T09:00:00Z'),
            dict(entity='project',
                 name='T_Tomsson_10_02',
                 title='Cancer exome',
                 customer='max_kaller',
                 status='defined',
                 timestamp='2011-02-01T12:00:00Z'),
            dict(entity='project',
                 name='T_Tomsson_10_03',
                 customer='joakim_lundeberg',
                 status='defined',
                 timestamp='2011-02-07T10:30:00Z')]

SAMPLES = [dict(entity='sample',
                name='S00001',
                customername='patient 1',
                project='T_Tomsson_10_02',
                received='2010-12-22T12:34:00Z',
                status='defined',
                timestamp='2010-12-22T12:34:00Z'),
           dict(entity='sample',
                name='S00002',
                customername='root 1',
                project='J_Johansson_10_01',
                received=None,
                status='defined',
                timestamp='2011-02-02T11:40:00Z')]


if __name__ == '__main__':
    map(put_document, ACCOUNTS.values())
    map(put_document, PROJECTS)
    map(put_document, SAMPLES)
