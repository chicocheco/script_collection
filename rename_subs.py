"""
Works with the following patterns:

The.Leftovers.S02E01.HDTV.x264-KILLERS.srt
Colony - 02x10 - The Garden of Beasts.FLEET.English.C.edit.Addic7ed.com.srt
Falling Skies - Season 5 - Ep. 01 - Find Your Warrior [HDTV.X264]-KiLLeRS.srt
"""

import os
import re
from pathlib import Path, PurePath
from collections import defaultdict
import pprint

EPISODE_RE = re.compile(r'(.?)(\d?\d)', re.IGNORECASE)

dd = defaultdict(dict)

for _, _, files in os.walk('.'):

    for file in files:

        if file.endswith('.mkv') or file.endswith('.mp4') or file.endswith('.avi'):
            # assuming that the first 2 pairs of digits indicate season + episode
            (s_lead, season), (e_lead, episode), *rest = EPISODE_RE.findall(file)
            season = season.zfill(2)
            episode = episode.zfill(2)
            dd[(season, episode)]['video'] = file

    for file in sorted(files):
        # sorting is needed to avoid processing new subs when a match had been found already
        if file.endswith('.srt'):
            (s_lead, season), (e_lead, episode), *rest = EPISODE_RE.findall(file)
            season = season.zfill(2)
            episode = episode.zfill(2)
            if (season, episode) in dd:
                if PurePath(dd[(season, episode)].get('video')).stem == PurePath(file).stem:
                    dd[(season, episode)]['sub'] = 'exist'
                else:
                    dd[(season, episode)]['sub'] = file
            else:
                print(f'No video found for: {file}')

# pprint.pprint(dd)

for value in dd.values():
    if len(value) > 1:
        if value['sub'] == 'exist':  # compare names without its extension
            print(f'\u2713 {value["video"]} already has correctly named subtitles.')
        else:
            video_filename = PurePath(value['video']).stem
            suff_sub = PurePath(value['sub']).suffix
            new_sub = video_filename + suff_sub
            print(f'{value["sub"]}  >>>  {new_sub}')
            Path(value['sub']).rename(new_sub)
    else:
        print(f'No subtitles found for {value.get("video")}')




