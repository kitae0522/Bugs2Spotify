import json
import datetime

from module import SpotifyApp
from module import SpotifyInfo
from module import TrackInfoUtils
from module import BugsApp


def run(source_playlist_id: str):
    with open('config.json', 'r') as config_file, open('result.json', 'r') as crawl_file:
        bugs_app = BugsApp()
        bugs_app.run(source_playlist_id)
        crawl_result = json.load(crawl_file)

        spotify_info = SpotifyInfo(json.load(config_file))
        spotify_app = SpotifyApp(spotify_info)

        playlist_title = crawl_result['title']
        playlist_id = spotify_app.create_playlist(playlist_name=playlist_title,
                                                  description=f'# Source Playlist Link: {bugs_app.playlist_url}')
        spotify_app.upload_playlist_thumbnail(playlist_id)
        print('✅ Create Playlist Successful')

        track_items = [
            TrackInfoUtils.set_track_info(*spotify_app.search(item['title'], item['artist']))
            for item in crawl_result['items']
        ]

        for idx, (track_id, _, _) in enumerate(track_items):
            print(f'{idx + 1}: {track_id}')

        for i in range(0, len(track_items), 50):
            batch_items = track_items[i:i + 50]
            spotify_app.append_items(playlist_id, batch_items)
        print('✅ Complete Task. Enjoy :)')


if __name__ == '__main__':
    source_playlist_id_list = (
        # '54990',
        # '25040',
        # '32592',
        # '62737',
        '42825',
    )
    for _id in source_playlist_id_list:
        run(_id)
