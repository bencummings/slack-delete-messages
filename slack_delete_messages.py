"""
Deletes all of the Slack messages (sans exclusions) for the specified user, and
optionally, within the specified channel only.

Four command line arguments are utilised. The first, which is required, is the
user ID, which consists of 9-11 uppercase alphanumeric characters and is
prefixed with 'U' or 'W'. The second, which is also required, is the user access
token, which consists of 76 lowercase alphanumeric characters and is prefixed
with 'xoxp'. The third, which is optional, is the channel ID, which consists of
9-11 uppercase alphanumeric characters and is prefixed with 'C' or 'D'. If
omitted, all messages will be deleted regardless of the channel. The fourth (and
final), which is also optional, is a whitespace separated list of timestamps for
messages that should be excluded (i.e. NOT deleted). Each timestamp represents
the total number of milliseconds since the Unix epoch (1970-01-01T00:00:00Z).

Usage:
    python slack_delete_messages.py --user-id <w> --token <x> [--channel <y>] [--exclude <z ...>]

Created by Ben Cummings on 2020-08-22.
"""


import re
import requests
import sys
import time


def main():
    # Removes this script's file name from the arguments list.
    del sys.argv[0]

    # Ensures that the user ID argument was specified and well-formed.
    if "--user-id" in sys.argv:
        try:
            # Ensures correct indexing/ordering.
            assert sys.argv[0] == "--user-id"

            # Sets the user ID.
            user_id = sys.argv[1]

            # Ensures that the user ID is a valid pattern.
            if not re.match(r"^[UW][0-9A-Z]{8,10}$", user_id):
                raise ValueError

            # Removes the user ID argument from the arguments list.
            del sys.argv[:2]
        except (AssertionError, IndexError, ValueError):
            print("Error. The user ID argument was malformed.", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error. The user ID argument wasn't specified.", file=sys.stderr)
        sys.exit(1)

    # Ensures that the token argument was specified and well-formed.
    if "--token" in sys.argv:
        try:
            # Ensures correct indexing/ordering.
            assert sys.argv[0] == "--token"

            # Sets the token.
            token = sys.argv[1]

            # Ensures that the token is a valid pattern.
            if not re.match(r"^xoxp-(?:\d{12}-){3}[0-9a-f]{32}$", token):
                raise ValueError

            # Removes the token argument from the arguments list.
            del sys.argv[:2]
        except (AssertionError, IndexError, ValueError):
            print("Error. The token argument was malformed.", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error. The token argument wasn't specified.", file=sys.stderr)
        sys.exit(1)

    # Determines if a channel was specified.
    # If so, only messages within the channel will be considered for deletion.
    if "--channel" in sys.argv:
        try:
            # Ensures correct indexing/ordering.
            assert sys.argv[0] == "--channel"

            # Sets the channel.
            channel = sys.argv[1]

            # Ensures that the channel is a valid pattern.
            if not re.match(r"^[CD][0-9A-Z]{8,10}$", channel):
                raise ValueError

            # Removes the channel argument from the arguments list.
            del sys.argv[:2]
        except (AssertionError, IndexError, ValueError):
            print("Error. The channel argument was malformed.", file=sys.stderr)
            sys.exit(1)
    else:
        channel = None

    # Determines if an exclusion list was specified.
    # Each exclusion should be the 16 digit suffix (which is the timestamp without the decimal point) of the message permalink.
    if "--exclude" in sys.argv:
        try:
            # Ensures correct indexing/ordering.
            assert sys.argv[0] == "--exclude"

            # Ensures that exclusions were actually specified.
            assert len(sys.argv[1:]) > 0

            # Sets the exclusions.
            exclusions = sys.argv[1:]

            # Ensures that the exclusions are valid patterns.
            for exclusion in exclusions:
                if not re.match(r"^\d{16}$", exclusion):
                    raise ValueError

            # Removes the exclude argument from the arguments list.
            del sys.argv[:]
        except (AssertionError, ValueError):
            print("Error. The exclude argument was malformed.", file=sys.stderr)
            sys.exit(1)
    else:
        exclusions = []

    # Sets the initial request headers.
    headers = {
        "content-type": "application/x-www-form-urlencoded"
    }

    # Sets the request query string parameters.
    params = {
        "token": token,
        "query": f"from:<@{user_id}>",
        "sort": "timestamp",
        "count": 100,
        "page": 1
    }

    # Requests and processes all of the messages authored by the specified user.
    messages = []

    while True:
        try:
            response = requests.get("https://slack.com/api/search.messages", headers=headers, params=params)

            # Determines if the request was successful (validity isn't determined at this point).
            if response.status_code == 200:
                response_body = response.json()

                # Determines if the request was valid.
                if response_body["ok"]:
                    if not response_body["messages"]["total"]:
                        print("There are no messages to process.")
                        break

                    # Processes the messages and extracts the data required for the deletion requests.
                    matches = response_body["messages"]["matches"]

                    for match in matches:
                        match_channel = match["channel"]["id"]
                        match_timestamp = match["ts"]

                        if (not channel or channel == match_channel) and match_timestamp.replace(".", "") not in exclusions:
                            messages.append({
                                "channel": match_channel,
                                "ts": match_timestamp
                            })

                    # Determines if the final chunk (i.e. page) of messages has been processed.
                    if params["page"] == response_body["messages"]["pagination"]["page_count"]:
                        print(f"Processed {len(messages)} messages.")
                        break

                    # Increments the page number for the subsequent request.
                    params["page"] += 1
                else:
                    print(f"Error. The request was unsuccessful. Message: {response_body['error']}.", file=sys.stderr)
                    sys.exit(1)
            else:
                print(f"Error. The request was unsuccessful. Status code: {response.status_code}.", file=sys.stderr)
                sys.exit(1)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            print("Error. Unable to connect to the Slack servers. Ensure that your network connection has internet connectivity and try again.", file=sys.stderr)
            sys.exit(1)

    # Updates the request headers.
    headers = {
        "content-type": "application/json; charset=UTF-8",
        "authorization": f"Bearer {token}"
    }

    # Requests the deletion of all of the messages authored by the specified user.
    count = 0

    for message in messages:
        # Sets the request body.
        data = {
            "channel": message["channel"],
            "ts": message["ts"],
            "as_user": True
        }

        # Repeats to avoid the current message being skipped when rate limiting occurs.
        while True:
            try:
                response = requests.post("https://slack.com/api/chat.delete", headers=headers, json=data)

                # Determines if the request was successful (validity isn't determined at this point).
                if response.status_code == 200:
                    response_body = response.json()

                    # Determines if the request was valid.
                    if response_body["ok"]:
                        count += 1

                        # Sends a progress update to standard out.
                        if not count % 10:
                            print(f"Deleted {count} messages.")

                        # Proceeds to the next message.
                        break
                    else:
                        print(f"Error. The delete request was unsuccessful. Message: {response_body['error']}.", file=sys.stderr)
                        sys.exit(1)
                # Determines if rate limiting has occurred.
                elif response.status_code == 429:
                    print("Error. Rate limit exceeded. Sleeping and trying again.", file=sys.stderr)
                    time.sleep(15)
                else:
                    print(f"Error. The delete request was unsuccessful. Status code: {response.status_code}.", file=sys.stderr)
                    sys.exit(1)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                print("Error. Unable to connect to the Slack servers. Ensure that your network connection has internet connectivity and try again.", file=sys.stderr)
                sys.exit(1)

    # OK.
    print(f"Successfully deleted {count} messages.")
    sys.exit(0)


if __name__ == "__main__":
    main()
