#!/usr/bin/env python3.8
import pprint
from collections import defaultdict
from datetime import datetime
import requests
from pathlib import Path
import json
from datetime import date
import rumps

import subprocess

STORAGE_PATH = Path('/tmp/suren')


def main(args):
    local_timezone = datetime.now().astimezone().tzinfo
    now = datetime.now(tz=local_timezone)
    start = now.replace(hour=3, minute=0, second=0, microsecond=0)
    start_f = start.isoformat()
    end_f = now.isoformat()
    if not STORAGE_PATH.is_file():
        STORAGE_PATH.write_text(json.dumps(dict()), encoding='utf-8')

    afk_status_to_sum = defaultdict(float)
    payload = {
        'query': [
            'afkbucket = "aw-watcher-afk_snihalan-mn2.linkedin.biz";',
            'not_afk = flood(query_bucket(afkbucket));',
            'not_afk = merge_events_by_keys(not_afk, ["status"]);',
            'RETURN = not_afk;'
        ],
        'timeperiods':
            [
                f'{start_f}/{end_f}'
            ]
    }
    response = requests.post('http://localhost:5600/api/0/query/', json=payload).json()
    for row in response:
        for a_row in row:
            status = a_row['data']['status']
            duration = a_row['duration']
            afk_status_to_sum[status] += duration
    afk_status_to_sum2 = dict()
    for k, v in afk_status_to_sum.items():
        afk_status_to_sum2[k] = (v / 60 / 60)
    notification_history = json.loads(STORAGE_PATH.read_text(encoding='utf-8'))
    notification_history2 = json.loads(STORAGE_PATH.read_text(encoding='utf-8'))
    for k, v in notification_history2.items():
        if v != date.today().isoformat():
            del notification_history[k]
    hours = afk_status_to_sum2.get('not-afk', 0.0)
    if hours >= 8.0:
        lower = int(hours)
        if notification_history.get(str(lower), '') != date.today().isoformat():
            subprocess.check_call(
                ['osascript', '-e', 'display notification "You\'ve reached your goal!" with title "Robot says"'])
            notification_history[lower] = date.today().isoformat()
    pprint.pprint(afk_status_to_sum2)


class StatusBarApp(rumps.App):
    def __init__(self):
        super(StatusBarApp, self).__init__('🐼', menu=['Pause'])
        self.timer = rumps.Timer(callback=main, interval=60 * 15)
        self.timer.start()

    @rumps.clicked('Pause')
    def pause_or_continue(self, sender):
        if sender.title == 'Pause':
            sender.title = 'Continue'
            self.timer.stop()
        elif sender.title == 'Continue':
            self.timer.start()
            sender.title = 'Pause'


if __name__ == '__main__':
    rumps.debug_mode(True)
    StatusBarApp().run()