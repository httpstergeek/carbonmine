# This file contains possible attributes and values you can use to configure carbonmine,
# sets connections string, user, name which is distributed to search heads.
#
# This is an carbonmine.conf in $SPLUNK_HOME/etc/carbonmin/default.  To set custom configurations,
# place an carbonmine.conf $SPLUNK_HOME/etc/carbonmin/local.

# GLOBAL SETTINGS
# Use the [global] stanza to define any global settings
#   * You can also define global settings outside of any stanza, at the top of the file.
#   * Each conf file should  have at most one global stanza, at the top of the file.
#   * If an attribute is define at both the global level and in a specific stanza, the
#     value in the specific stanza takes precedence.


[global]
proxy_url = <url>:<port>|<url>
* set proxy server,  optional.
* EXAMPLE:  proxy.foo.com:8080 or proxy.foo.com

proxy_user = <string>
* set proxy user, optional.

proxy_password = <string>
* set proxy user password, optional.

#*******
# GENERAL SETTINGS:
# This following attribute/value pairs are valid for all stanzas.  The [production] stanza
# is required. Additional stanzas can be define which can be used by user by specifying instance=<string>.
# This is if your environment has multiple Graphite instances
#*******


[<instance>]
url = http(s)://fqdn
* sets server for Graphite instance.
* EXAMPLE: http://graphite.mycompany.com

user = graphite User
* sets user for Graphite instance, optional.  Only required if you have enabled authentication for graphite.

password = graphite user password
* set password for Graphite user, optional.  Must define user.



