import json
import datetime
from urllib.parse import urlparse

from module import SpotifyApp
from module import SpotifyInfo
from module import TrackInfoUtils
from module import BugsApp


def run(source_playlist_id: str):
    try:
        with open('config.json', 'r') as config_file:
            # Step1. Playlist Crawling
            bugs_app = BugsApp()
            crawl_is_err, crawl_msg, crawl_result = bugs_app.run(source_playlist_id)
            print(crawl_msg)
            if crawl_is_err:
                raise Exception(crawl_msg)

            # Step2. Spotify API Connect
            spotify_info = SpotifyInfo(json.load(config_file))
            spotify_app = SpotifyApp(spotify_info)

            # Step3. Make Spotify Playlist
            playlist_title = crawl_result['title']
            make_playlist_is_err, make_playlist_msg, playlist_id = spotify_app.create_playlist(
                playlist_name=playlist_title,
                description=f'# Source Playlist Link: {bugs_app.playlist_url}')
            print(make_playlist_msg)
            if make_playlist_is_err:
                raise Exception(make_playlist_msg)

            # Step4. Upload Playlist Thumbnail Image
            upload_thumbnail_is_err, upload_thumbnail_msg = spotify_app.upload_playlist_thumbnail(playlist_id)
            print(upload_thumbnail_msg)
            if upload_thumbnail_is_err:
                raise Exception(upload_thumbnail_msg)

            # Step5. Find Track from Bugs Playlist
            track_items = []
            for item in crawl_result['items']:
                search_track_is_err, search_track_msg, search_track_res = spotify_app.search(item['title'],
                                                                                             item['artist'])
                print(search_track_msg)
                if not search_track_is_err:
                    track_items.append(TrackInfoUtils.set_track_info(*search_track_res))
                else:
                    raise Exception(search_track_msg)

            # Step6. Append Track that found
            for i in range(0, len(track_items), 50):
                batch_items = track_items[i:i + 50]
                append_is_err, append_msg = spotify_app.append_items(playlist_id, batch_items)
                print(append_msg)
                if append_is_err:
                    raise Exception(append_msg)

            print('✅ Enjoy :)')
    except Exception as err:
        pass


if __name__ == '__main__':
    bugs_playlist_url = input('|> 벅스 플레이리스트 주소를 입력하세요: ')
    run(urlparse(bugs_playlist_url).path.split('/')[-1])
