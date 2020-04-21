[![Build Status](https://travis-ci.org/hpe-container-platform-community/hpecp-client.svg?branch=master)](https://travis-ci.org/hpe-container-platform-community/hpecp-client)
[![Issues](https://img.shields.io/github/issues/hpe-container-platform-community/hpecp-client/bug.svg)](https://github.com/hpe-container-platform-community/hpecp-client/issues?q=is%3Aissue+is%3Aopen+label%3A"bug")
[![Coverage Status](https://coveralls.io/repos/github/hpe-container-platform-community/hpecp-client/badge.svg?branch=master)](https://coveralls.io/github/hpe-container-platform-community/hpecp-client?branch=master)

[![Coverage Status](https://coveralls.io/repos/github/hpe-container-platform-community/hpecp-client/badge.svg)](https://coveralls.io/github/hpe-container-platform-community/hpecp-client)

[![Pyversions](https://img.shields.io/badge/Pyversions-2.7,%203.5,%203.6,%203.7-green.svg)](https://github.com/hpe-container-platform-community/hpecp-client/blob/master/tox.ini#L7)
[![Apache2 license](http://img.shields.io/badge/license-apache2-brightgreen.svg)](http://opensource.org/licenses/Apache-2.0)

----

This project is a prototype - not much to see here yet!

## Installation

pip install --upgrade git+https://github.com/hpe-container-platform-community/hpecp-client@master

## Logging

Log level is controlled with the environment variable `LOG_LEVEL`.

You may set it programmatically in your code:

```
os.environ["LOG_LEVEL"] = "DEBUG"
```

Typical valid values are `ERROR`, `WARNING`, `INFO`, `DEBUG`. For a full list of values, see [here](https://docs.python.org/3/library/logging.html#logging-levels)

## Basic Usage

```
from hpecp import ContainerPlatformClient

client = ContainerPlatformClient(username='hpecp_username', 
                                password='hpecp_password', 
                                api_host='hpecp_controller_ip', 
                                api_port='hpecp_controller_port',
                                use_ssl=True)

client.create_session()

# TODO - the following hasn't been implemented yet

client.epic_tenant.list()
```