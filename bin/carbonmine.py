# encoding: utf-8
# Author: Bernardo Macias <bmacias@httpstergeek.com>
#
#
# All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import util
import re
import json
from logging import INFO
from splunklib.searchcommands import \
    dispatch, GeneratingCommand, Configuration, Option, validators

__author__ = 'Bernardo Macias '
__credits__ = ['Bernardo Macias']
__license__ = "ASF"
__version__ = "2.0"
__maintainer__ = "Bernardo Macias"
__email__ = 'bmacias@httpstergeek.com'
__status__ = 'Production'

logger = util.setup_logger(INFO)


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


@Configuration()
class carbonMineCommand(GeneratingCommand):
    earliest = Option(
        doc='''**Syntax:** **virtualServers=***<string>*
         **Description:** starting time for query. ''',
        require=False)

    latest = Option(
        doc='''**Syntax:** **getStats=***boolean*
         **Description:** finish time for query.''',
        require=False)

    target = Option(
        doc='''**Syntax:** **partition=***<string>*
         **Description:** Graphite object/path. ''',
        require=True, validate=validators.List())

    instance = Option(
        doc='''**Syntax:** **device=***<string>*
         **Description:** stanza name of instance. Defaults to prod. ''',
        require=False)

    def generate(self):
        # get config and command arguments
        instance = self.instance if self.instance else 'production'
        conf = util.getstanza('carbonmine', instance)
        timeout = int(conf['timeout']) if 'timeout'in conf else 60
        earliest = 'from={0}'.format(self.earliest) if self.earliest else None
        latest = 'until={0}'.format(self.latest) if self.latest else None
        url = '{0}/render?{1}&{2}'.format(conf['url'], earliest, latest)

        for target in self.target:
            rurl = '{0}&target={1}&format=json'.format(url, target.strip())
            for record in get_target_data(rurl, timeout=timeout):
                yield record

dispatch(carbonMineCommand, sys.argv, sys.stdin, sys.stdout, __name__)
