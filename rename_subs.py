import os
import re
from pathlib import Path, PurePath
from collections import defaultdict
import pprint

EPISODE_RE = re.compile(r'S\d\dE\d\d', re.IGNORECASE)

# samples:
# The.Leftovers.S02E01.HDTV.x264-KILLERS.srt
# Falling.Skies.S05E01.HDTV.x264-KILLERS.mp4
# TODO: Falling Skies - Season 5 - Ep. 01 - Find Your Warrior [HDTV.X264]-KiLLeRS.srt

dd = defaultdict(dict)

for _, _, files in os.walk('.'):
    
    for file in files:
        # print(file)
        if file.endswith('.mkv') or file.endswith('.mp4') or file.endswith('.avi'):
            match = EPISODE_RE.search(file).group().capitalize()
            dd[match]['video'] = file

        elif file.endswith('.srt'):
            match = EPISODE_RE.search(file).group().capitalize()
            # do not override if 'sub' already exists
            if not dd.get(match, {}).get('sub'):
                dd[match]['sub'] = file

# for debugging
# pprint.pprint(dd)

for value in dd.values():
    if len(value) > 1:
        if PurePath(value['video']).stem == PurePath(value["sub"]).stem:
            print(f'\u2713 {value["video"]} already has correctly named subtitles.')
        else:
            video_filename = PurePath(value['video']).stem
            suff_sub = PurePath(value['sub']).suffix
            new_sub = video_filename + suff_sub
            print(f'{value["sub"]}  >>>  {new_sub}')
            Path(value['sub']).rename(new_sub)
    else:
        if value['sub']:
            print(f'\t No video file found for {value["sub"]}')
        else:
            print(f'No subtitles found for {value["video"]}')




