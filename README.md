Carbon Mine - A Splunk Search Command for Graphite
=================

Carbon Mine is a Splunk Search command that uses Graphites render url api and retrieves raw json data.
This Splunk utilizes requests python modules.

##Supports:
* Supports multiple graphite Instances

* Proxy support


Requirements
---------

* This version has been test on 6.x and should work on 5.x.

* App is known to work on Linux,and Mac OS X, but has not been tested on other operating systems. Window should work

* App requires network access to Graphite Server

* Miminum of 2 GB RAM and 1.8 GHz CPU.



Prerequisites
---------
* Graphite 9.x or Higher

* Splunk version 6.x or Higher

You can download it [Splunk][splunk-download].  And see the [Splunk documentation][] for instructions on installing and more.
[Splunk]:http://www.splunk.com
[Splunk documentation]:http://docs.splunk.com/Documentation/Splunk/latest/User
[splunk-download]:http://www.splunk.com/download


Installation instructions
---------

1) copy repo into $SPLUNK_HOME/etc/apps/.

2) create $SPLUNK_HOME/etc/apps/carbonmin/local/carbonmine.conf.

3) configure [production] stanza with url to graphite instance. Note: if proxy look at README for proxy config.

Example Command
---------

`| carbonmine earliest=-1hour latest=now target=nonNegativeDerivative(*.elasticsearch.indices._all.search.query_total)
    OR
`| carbonmine target=nonNegativeDerivative(*.elasticsearch.indices._all.search.query_total)
    OR
`| carbonmine target=nonNegativeDerivative(*.elasticsearch.indices._all.search.query_total) instance=dev

Recommendations
---------

It is recommend that this be installed on an Search head.
