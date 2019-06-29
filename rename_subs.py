import os
import re
from pathlib import Path, PurePath
from collections import defaultdict
import pprint

# TODO: mozna nepotrebuju S x E vubec hledat
EPISODE_RE = re.compile(r'(S)?(\d\d)(x)?(E)?(\d\d)', re.IGNORECASE)

# samples:
# The.Leftovers.S02E01.HDTV.x264-KILLERS.srt
# Falling.Skies.S05E01.HDTV.x264-KILLERS.mp4
# TODO: Falling Skies - Season 5 - Ep. 01 - Find Your Warrior [HDTV.X264]-KiLLeRS.srt

dd = defaultdict(dict)

for _, _, files in os.walk('.'):

    for file in files:

        if file.endswith('.mkv') or file.endswith('.mp4') or file.endswith('.avi'):
            season, num_season, x, episode, num_episode = EPISODE_RE.search(file).groups()
            dd[(num_season, num_episode)]['video'] = file  # store video file name

    for file in sorted(files):
        if file.endswith('.srt'):
            season, num_season, x, episode, num_episode = EPISODE_RE.search(file).groups()
            # TODO: check whether a matching subtitles exist already

            if (num_season, num_episode) in dd:
                if PurePath(dd[(num_season, num_episode)].get('video')).stem == PurePath(file).stem:
                    dd[(num_season, num_episode)]['sub'] = 'exist'
                else:
                    dd[(num_season, num_episode)]['sub'] = file
            else:
                print(f'No video found for {file}.')



# for debugging
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




