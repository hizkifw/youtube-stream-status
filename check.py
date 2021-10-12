import sys
import re
import json
import time
from datetime import datetime
from urllib import request

def get_metadata(video_id, api_key):
    data = json.dumps({
        'videoId': video_id,
        'context': {
            'client': {
                'utcOffsetMinutes': 540,
                'clientName': 'WEB',
                'clientVersion': '2.20211009.11.00',
                'hl': 'en',
                'gl':'JP',
                'timeZone':'Asia/Tokyo',
            },
        },
    }).encode('utf8')

    req = request.Request('https://www.youtube.com/youtubei/v1/updated_metadata?key={}'.format(api_key), data=data)
    req.add_header('Content-Type', 'application/json')
    res = request.urlopen(req)
    return json.loads(res.read().decode('utf8'))

def is_stream_online(url, quiet=False, wait=False, verbose=False):
    # Fetch video page
    if not quiet:
        print('Fetching YouTube page...')
    youtube_page = request.urlopen(url).read().decode('utf8')
    regex_canonical = r"<link rel=\"canonical\" href=\"https://www\.youtube\.com/watch\?v=(.{11})\">"
    regex_api_key = r"\"innertubeApiKey\":\"([^\"]+)\""

    # Get details
    video_id = re.findall(regex_canonical, youtube_page, re.MULTILINE)[0]
    api_key = re.findall(regex_api_key, youtube_page, re.MULTILINE)[0]

    if verbose:
        print('Video ID:', video_id)
        print('Found API Key', api_key)

    # Send heartbeat
    if not quiet:
        print('Checking for stream status')

    while True:
        heartbeat = get_metadata(video_id, api_key)
        if verbose:
            print(json.dumps(heartbeat, indent=2))

        reason = None
        for action in heartbeat['actions']:
            if 'updateDateTextAction' in action:
                reason = action['updateDateTextAction']['dateText']['simpleText']

        is_online = 'streaming' in reason or 'in progress' in reason

        if not quiet:
            print(reason)

        if not wait or is_online:
            return is_online

        time.sleep(5)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("""youtube-stream-status

Usage: {} [options] <youtube url>
 -q, --quiet  Do not output anything to stdout
 -w, --wait   Keep polling until the stream starts, then exit
 --verbose    Print heartbeat to stdout for debugging
""".format(sys.argv[0]))
        sys.exit(1)
    url = sys.argv[-1]
    quiet = '-q' in sys.argv or '--quiet' in sys.argv
    wait = '-w' in sys.argv or '--wait' in sys.argv
    verbose = '--verbose' in sys.argv
    if is_stream_online(url, quiet, wait, verbose):
        sys.exit(0)
    sys.exit(2)
