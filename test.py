# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
import json

if __name__ == '__main__':
    # print >> sys.stderr, json.dumps(sys.argv)
    print >> sys.stderr, 'Some log message'
    print json.dumps(sys.argv)
    sys.exit(1)
