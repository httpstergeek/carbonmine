__author__ = 'berniem'
import os
import logging
import logging.handlers
import sys
import json
from platform import system
from splunk.clilib import cli_common as cli
from splunklib.searchcommands import \
    dispatch, GeneratingCommand, Configuration, Option

platform = system().lower()

# Loading eggs into python execution path
if platform == 'darwin':
    platform = 'macosx'
running_dir = os.path.dirname(os.path.realpath(__file__))
egg_dir = os.path.join(running_dir, 'eggs')
for filename in os.listdir(egg_dir):
    file_segments = filename.split('-')
    if filename.endswith('.egg'):
        filename = os.path.join(egg_dir, filename)
        if len(file_segments) <= 3:
            sys.path.append(filename)
        else:
            if platform in filename:
                sys.path.append(filename)

import requests


def setup_logger(level):
    """
    setups logger
    :param level: Logging level
    :return: logger object
    """
    logger = logging.getLogger('carbonmine')
    logger.propagate = False  # Prevent the log messages from being duplicated in the python.log file
    logger.setLevel(level)
    file_handler = logging.handlers.RotatingFileHandler(os.path.join('carbonmine.log'), maxBytes=5000000,
                                                        backupCount=5)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    consolehandler = logging.StreamHandler()
    consolehandler.setFormatter(formatter)
    logger.addHandler(consolehandler)
    return logger


def getstanza(conf, stanza):
    """
    Returns dict object of config file settings
    :param conf: Splunk conf file name
    :param stanza: stanza (entry) from conf file
    :return: returns dictionary of setting
    """
    appdir = os.path.dirname(os.path.dirname(__file__))
    conf = "%s.conf" % conf
    apikeyconfpath = os.path.join(appdir, "default", conf)
    apikeyconf = cli.readConfFile(apikeyconfpath)
    localconfpath = os.path.join(appdir, "local", conf)
    if os.path.exists(localconfpath):
        localconf = cli.readConfFile(localconfpath)
        for name, content in localconf.items():
            if name in apikeyconf:
                apikeyconf[name].update(content)
            else:
                apikeyconf[name] = content
    return apikeyconf[stanza]


def setproxy(local_conf, global_conf):
    """
    Sets up dict object for proxy settings
    :param local_conf:
    :param global_conf:
    :return:
    """
    proxy = None
    proxy_url = global_conf['proxy_url'] if 'proxy_url' in global_conf else None
    proxy_url = local_conf['proxy_url'] if 'proxy_url' in local_conf else proxy_url
    if proxy_url:
        proxy = dict()
        proxy_user = global_conf['proxy_user'] if 'proxy_user' in global_conf else None
        proxy_user = local_conf['proxy_user'] if 'proxy_user' in local_conf else proxy_user
        proxy_password = global_conf['proxy_password'] if 'proxy_password' in global_conf else None
        proxy_password = local_conf['proxy_password'] if 'proxy_password' in local_conf else proxy_password
        if proxy_password and proxy_user:
            proxy_url = '%s:%s@%s' % (proxy_user, proxy_password, proxy_url)
        elif proxy_user and not proxy_password:
            proxy_url = '%s@%s' % (proxy_user, proxy_url)
        elif not proxy_user and not proxy_password and proxy_url:
            proxy_url = '%s' % proxy_url
        else:
            proxy = None
        if proxy:
            proxy['https'] = 'https://%s' % proxy_url
            proxy['http'] = 'http://%s' % proxy_url
    return proxy


def tojson(jmessage):
    """
    Returns a pretty print json string
    :param jmessage: dict object
    :return: str
    """
    jmessage = json.dumps(json.loads(json.JSONEncoder().encode(jmessage)),
                          indent=4,
                          sort_keys=True,
                          ensure_ascii=True)
    return jmessage


@Configuration()
class carbonMineCommand(GeneratingCommand):
    """ %(synopsis)

    ##Syntax

    .. code-block::
    carbonmine earliest="<time>" latest="<time>" target="<string>" instance=<string>

    ##Description

    Return json events for every data point return for each target returned.

    ##Example

    Return a graphite API Json objects for a target.

    .. code-block::
        | carbonmine earliest="-1hour" latest="now" target="nonNegativeDerivative(*.elastic.*._all.search.query_total)"

    """

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
        require=True)

    instance = Option(
        doc='''**Syntax:** **device=***<string>*
         **Description:** stanza name of instance. Defaults to prod. ''',
        require=False)

    def generate(self):
        logger = setup_logger(logging.INFO)

        try:
            # get config and command arguments
            instance = self.instance if self.instance else 'production'
            conf = getstanza('carbonmine', instance)
            proxy_conf = getstanza('carbonmine', 'global')
            proxies = setproxy(conf, proxy_conf)
            auth = (conf['user'], conf['password']) if ('user' in conf and 'password' in conf)else None
            server = conf['server']
            query = list()
            if self.earliest:
                query.append('from=%s' % self.earliest)
            if self.latest:
                query.append('until=%s' % self.latest)
            if self.target:
                query.append('target=%s' % self.target)
            query.append('format=json')
            timeout = int(conf['timeout']) if 'timeout'in conf else 60
            # building url string
            query = '&'.join(query)
            server = '%s%s%s' % (server, '/render?', query)

            # retrieving data from Graphite API
            graphite_request = requests.get(server, auth=auth, headers={'Accept': 'application/json'},
                                            timeout=timeout, proxies=proxies)
            graphite_data = graphite_request.json()
        except Exception as e:
            logger.debug('carbonMineCommand: %s' % e)
            yield {'error': e}
            exit()

        if graphite_request.status_code == 200:
            # for each returned target
            for data in graphite_data:
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
                    record['source'] = self.target
                    record['value'] = value
                    record['target'] = graphite_target
                    record['function'] = graphite_function
                    record['_raw'] = tojson(record)
                    yield record
        else:
            # If not 200 status_code show error message in Splunk UI
            record = dict()
            record['status'] = graphite_request.status_code
            record['error'] = graphite_data
            record['_raw'] = tojson(record)
            logger.debug('carbonMineCommand: Recieved status code=%s' % record['status'], record['error'])
            yield record

dispatch(carbonMineCommand, sys.argv, sys.stdin, sys.stdout, __name__)