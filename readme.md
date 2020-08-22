# Introduction

This script bulk deletes all of the Slack messages (sans exclusions) for the specified user, and optionally, within the specified channel only.


# Requirements

The deletion process requires an internet connection that allows HTTPS requests on port 443, as well as a Python 3.8.5 (or greater) installation with the following third-party package:

* Requests 2.24.0

Presuming that the Python interpreter is accessible via the `$PATH` environment variable, the above package can be installed via the command prompt or terminal with `python -m pip install requests`.


# Usage

`python slack_delete_messages.py --user-id <w> --token <x> [--channel <y>] [--exclude <z ...>]`

Four command line arguments are utilised. The first, which is required, is the user ID, which consists of 9-11 uppercase alphanumeric characters and is prefixed with 'U' or 'W'. The second, which is also required, is the user access token, which consists of 76 lowercase alphanumeric characters and is prefixed with 'xoxp'. The third, which is optional, is the channel ID, which consists of 9-11 uppercase alphanumeric characters and is prefixed with 'C' or 'D'. If omitted, all messages will be deleted regardless of the channel. The fourth (and final), which is also optional, is a whitespace separated list of timestamps for messages that should be excluded (i.e. NOT deleted). Each timestamp represents the total number of milliseconds since the Unix epoch (1970-01-01T00:00:00Z).


# History

Updated by Ben Cummings on 2020-08-22.