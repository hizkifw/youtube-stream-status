import sys
import re
import json
import time
from urllib import request

def send_heartbeat(video_id, api_key):
    data = json.dumps({
        "videoId":video_id,
        "context":{"client":{"utcOffsetMinutes":480,"deviceMake":"www","deviceModel":"www","browserName":"Chrome","browserVersion":"84.0.4147.89","osName":"Windows","osVersion":"10.0","clientName":"WEB","clientVersion":"2.20200728.05.00","hl":"en","gl":"SG","timeZone":"Asia/Makassar"},"request":{}},"heartbeatRequestParams":{"heartbeatChecks":["HEARTBEAT_CHECK_TYPE_LIVE_STREAM_STATUS"]}
    }).encode('utf8')
    req = request.Request("https://www.youtube.com/youtubei/v1/updated_metadata?key={}".format(api_key), data=data)
    req.add_header('Content-Type', 'application/json')
    res = request.urlopen(req)
    return json.loads(res.read().decode('utf8'))

def is_stream_online(url, quiet=False, wait=False, debug=False):
    # Fetch video page
    if not quiet:
        print("Fetching YouTube page...")
    youtube_page = request.urlopen(url).read().decode('utf8')
    regex_canonical = r"<link rel=\"canonical\" href=\"https://www\.youtube\.com/watch\?v=(.{11})\">"

    # Get details
    video_id = re.findall(regex_canonical, youtube_page, re.MULTILINE)[0]
    api_key = re.findall(r"\"innertubeApiKey\":\"([^\"]+)\"", youtube_page, re.MULTILINE)[0]

    # Send heartbeat
    if not quiet:
        print("Checking for stream status")

    while True:
        heartbeat = send_heartbeat(video_id, api_key)
        if debug:
            print(json.dumps(heartbeat, indent=2))

        reason = None
        for action in heartbeat['actions']:
            if 'updateDateTextAction' in action:
                reason = action['updateDateTextAction']['dateText']['simpleText']

        is_online = 'streaming' in reason

        if not quiet:
            print(reason)

        if not wait or is_online:
            return is_online

        poll_delay = 5
        time.sleep(poll_delay)

if __name__ == "__main__":
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
