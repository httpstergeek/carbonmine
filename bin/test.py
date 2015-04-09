
__author__ = ''

import sys
import re
import util
import json
import Queue

def get_target_data(url, username=None, password=None, data=None, proxy=None, timeout=None):
    print url
    connection = request(url, username=username, password=password,
                         data=data, headers={'Accept': 'application/json'},
                         timeout=timeout, proxy=proxy)
    return connection


def get_target_data(url, username=None, password=None, data=None, proxy=None, timeout=None):
    graphite_data = util.request(url, username=username, password=password,
                              data=data, headers={'Accept': 'application/json'},
                              timeout=timeout, proxy=proxy)

    match = re.match(r'^[^/]+//(?P<source>[^/]+)', url)
    source = match.group('source')
    if graphite_data['code'] == 200:
        # for each returned target
        targets = json.loads(graphite_data['msg'])
        for data in targets:
            target_name = data['target'].rstrip(')').split('(')
            # checking if function was used in query
            if len(target_name) == 2:
                graphite_function = target_name[0]
                graphite_target = target_name[1]
            else:
                graphite_target = target_name[0]
                graphite_function = 'None'
            # for each data point in target create record
            for data_point in data['datapoints']:
                value, epoch = data_point
                record = dict()
                record['_time'] = epoch
                record['sourcetype'] = 'graphite'
                record['source'] = source
                record['value'] = value
                record['target'] = graphite_target
                record['function'] = graphite_function
                record['_raw'] = util.tojson(record)
                yield record
    else:
        # If not 200 status_code show error message in Splunk UI
        record = dict()
        record['status'] = graphite_data['code']
        record['url'] = url
        record['error'] = graphite_data
        record['_raw'] = util.tojson(record)
        yield record



url = 'http://lyn-graphite.zillow.local'
earliest='now'
latest='-24h'
target2='webstats.del.pre.lyn.zweb.top.homedetails.pct99'
target='webstats.del.pre.lyn.zweb.top.homedetails.pct95'
url = '{0}/render?from={1}&until={2}'.format(url, earliest, latest)
target = '{0}&target={1}&format=json'.format(url, target2)
for x in get_target_data(target):
    print x
