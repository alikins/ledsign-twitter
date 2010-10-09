#!/usr/bin/env python

"""
twitter-repeater is a bot that automatically retweets any tweets in which its name
is "mentioned" in. In order for a tweet to be retweeted, the bot account must be
following the original user who tweeted it, that user must not be on the ignore
list, and the tweet must pass some basic quality tests.

The idea was originally inspired by the @SanMo bot and was created so I could use
something similar for New London, CT (@NLCT)

It runs well on Linux but it should run just as well on Mac OSX or Windows.

I use the following user Cron job to run the bot every 5 minutes:

*/5     *       *       *       *       $HOME/twitter-repeater/repeater.py
"""

# Project: twitter-repeater
# Author: Charles Hooper <chooper@plumata.com>
#
# Copyright (c) 2010, Charles Hooper
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, 
# are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# * Neither the name of Plumata LLC nor the names of its contributors may be
# used to endorse or promote products derived from this software without specific prior
# written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

# imports

import sys
import tweepy
import settings
import webbrowser
import cgi
import time

# import exceptions
from urllib2 import HTTPError

# this sign model to drive the sign
import signmodule

# globals - The following is populated later by load_lists
IGNORE_LIST = []
FILTER_WORDS = []

def debug_print(text):
    """Print text if debugging mode is on"""
    if settings.debug:
        print text


def get_last_id(statefile):
    """Retrieve last status ID from a file"""

    debug_print('Getting last ID from %s' % (statefile,))
    try:
        f = open(statefile,'r')
        id = int(f.read())
        f.close()
    except IOError:
        debug_print('IOError raised, returning zero (0)')
        return 0
    debug_print('Got id %d' % (id,))
    return id


def save_id(statefile,id):
    """Save last status ID to a file"""
    last_id = get_last_id(statefile)

    if last_id < id:
        debug_print('Saving new ID %d to %s' % (id,statefile))
        f = open(statefile,'w')
        f.write(str(id)) # no trailing newline
        f.close()
    else:
        debug_print('Received smaller ID, not saving. Old: %d, New: %s' % (
            last_id, id))


def load_lists(force=False):
    """Load ignore and filtered word lists"""
    debug_print('Loading ignore list')
    if not IGNORE_LIST or force is True:
        global IGNORE_LIST
        IGNORE_LIST = [
            line.lower().strip() for line in open(settings.ignore_list) ]

    debug_print('Loading filtered word list')
    if not FILTER_WORDS or force is True:
        global FILTER_WORDS
        FILTER_WORDS = [
            line.lower().strip() for line in open(settings.filtered_word_list) ]

def careful_retweet(api,reply):
    """Perform retweets while avoiding loops and spam"""

    load_lists()

    debug_print('Preparing to display #%d' % (reply.id,))
    debug_print('reply: %s' % reply)
    normalized_tweet = reply.text.lower().strip()

   # Don't try to retweet our own tweets
    if reply.user.screen_name.lower() == settings.username.lower():
        return

    # Don't retweet if the tweet is from an ignored user
    if reply.user.screen_name.lower() in IGNORE_LIST:
        return

    # Don't retweet if the tweet contains a filtered word
    for word in normalized_tweet.split():
        if word.lower().strip() in FILTER_WORDS:
            return

    # HACK: Don't retweet if tweet contains more usernames than words (roughly)
    username_count = normalized_tweet.count('@')
    if username_count >= len(normalized_tweet.split()) - username_count:
        return

    # Try to break retweet loops by counting the occurences tweeting user's name
    if normalized_tweet.split().count('@'+ reply.user.screen_name.lower()) > 0:
        return


    print "\n", reply.user.screen_name.lower()
    print reply.text

    sign = signmodule.Sign("/dev/tty.KeySerial1")
    sign.show("%s: %s\n" % (reply.user.screen_name.lower(), reply.text)) 
#    debug_print('Retweeting #%d' % (reply.id,))
    #status = api.retweet(id=reply.id)
    #print "status", status
    #return status


def main():
    run_auth = False
    if len(sys.argv) > 1 and sys.argv[1] == "--auth":
        run_auth = True

#    sign = signmodule.Sign("/dev/tty.KeySerial1")

    auth = tweepy.OAuthHandler(consumer_key=settings.consumer_key,
	consumer_secret=settings.consumer_secret)

    if run_auth:
        try:
            redirect_url = auth.get_authorization_url()
        except tweepy.TweepError:
            print 'Error! Failed to get request token.'

        print redirect_url

        # Open authorization URL in browser
        webbrowser.open(auth.get_authorization_url())

        # Ask user for verifier pin
        pin = raw_input('Verification pin number from twitter.com: ').strip()

        access_token = auth.get_access_token(pin)
        
        print access_token.to_string()
        print dir(access_token)
        (secret, key) = cgi.parse_qsl(access_token.to_string())
        settings.access_token_key = key[1]
        settings.access_token_secret = secret[1]
        print "access_token_key", settings.access_token_key
        print "access_token_secret", settings.access_token_secret

 #   access_key, access_secret = cgi.parse_qsl(access_token)
    auth.set_access_token(settings.access_token_key, settings.access_token_secret)
    
    api = tweepy.API(auth_handler=auth, secure=True, retry_count=3)

    print "User: ", api.me(), dir(api.me())
    last_id = get_last_id(settings.last_id_file)

    debug_print('Loading friends list')
    friends = api.friends_ids()
    debug_print('Friend list loaded, size: %d' % len(friends))


    while True:
        try:
            debug_print('Retrieving mentions')
            replies = api.mentions()
	    print replies
        except Exception, e:    # quit on error here
            print e

            print "\n\n\n what the heck just happend? \n\n\n"
	    #chill out for a while, then try again
	    time.sleep(300)
            continue

        # want these in ascending order, api orders them descending
        replies.reverse()
        print "replies", replies
        print "lastid: ", last_id

        for reply in replies:
            print "reply.id: ", reply.id
            # ignore tweet if it's id is lower than our last tweeted id
#            if reply.id > last_id and reply.user.id in friends:
            if reply.id > last_id:
                try:
                    print "reply", reply, type(reply), dir(reply)
                    careful_retweet(api,reply)
                except HTTPError, e:
                    print e.code()
                    print e.read()
		    raise
                except Exception, e:
                    print 'e: %s' % e
                    print repr(e)
		    raise
                else:
                    print "saving id file", reply.id
                    save_id(settings.last_id_file,reply.id)

        # twitter api is rate limited to 350 requests an hour...
        time.sleep(settings.interval)

    debug_print('Exiting cleanly')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        quit()

