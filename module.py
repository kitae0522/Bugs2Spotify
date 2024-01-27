import datetime
import json
import base64
from typing import List

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import requests
from bs4 import BeautifulSoup


class Utils:
    @staticmethod
    def string_inject(string_items, sep=' '):
        return sep.join(string_items)


class TrackInfo:
    def __init__(self, track_id, track_title, track_artist):
        self.id = track_id
        self.title = track_title
        self.artist = track_artist

    def __iter__(self):
        yield self.id
        yield self.title
        yield self.artist


class TrackInfoUtils:
    @staticmethod
    def set_track_info(track_id, track_title, track_artist):
        return TrackInfo(track_id, track_title, track_artist)

    @staticmethod
    def get_convert_dict(track_info):
        _track_id, _track_title, _track_artist = track_info
        return {'id': _track_id, 'title': _track_title, 'artist': _track_artist}

    def get_convert_track_info(self, track_info_dict):
        _track_id = track_info_dict.get('id', None)
        _track_title = track_info_dict.get('title', None)
        _track_artist = track_info_dict.get('artist', None)
        return self.set_track_info(_track_id, _track_title, _track_artist)


class ReturnClass:
    def __init__(self, _is_error, _message):
        self.is_error = _is_error
        self.message = _message

    def __iter__(self):
        yield self.is_error
        yield self.message


class ReturnClassWithResult(ReturnClass):
    def __init__(self, _is_error, _message, _result):
        super().__init__(_is_error, _message)
        self.result = _result

    def __iter__(self):
        yield self.is_error
        yield self.message
        yield self.result


class SpotifyInfo:
    def __init__(self, config):
        self.CLIENT_ID = config.get('client_id', None)
        self.CLIENT_SECRET = config.get('client_secret', None)
        self.REDIRECT_URI = config.get('redirect_uri', None)
        self.USER_ID = config.get('user_id', None)

    def __iter__(self):
        yield self.CLIENT_ID
        yield self.CLIENT_SECRET
        yield self.REDIRECT_URI
        yield self.USER_ID


class SpotifyApp:
    def __init__(self, api_info):
        self.utils = Utils()
        self.scope = ('playlist-modify-public', 'ugc-image-upload')
        self.SPOTIFY_API_INFO = api_info
        self.SPOTIFY_OAUTH = SpotifyOAuth(scope=self.utils.string_inject(self.scope),
                                          client_id=self.SPOTIFY_API_INFO.CLIENT_ID,
                                          client_secret=self.SPOTIFY_API_INFO.CLIENT_SECRET,
                                          redirect_uri=self.SPOTIFY_API_INFO.REDIRECT_URI)
        self.parent = spotipy.Spotify(auth_manager=self.SPOTIFY_OAUTH)

    def search(self, track: str, artist: str) -> ReturnClassWithResult:
        search_query = (track, artist)  # Priority Setting
        search_result = self.parent.search(type='track', q=self.utils.string_inject(search_query), market='KR')
        if search_result['tracks']['total'] > 0:
            track_list = search_result['tracks']['items']
            first_track = track_list[0]
            track_info = TrackInfoUtils.set_track_info(track_id=first_track['id'],
                                                       track_title=first_track['name'],
                                                       track_artist=first_track['album']['artists'][0]['name'])
            return_class_message = f'|> {track_info.artist} 아티스트의 {track_info.title} 트랙을 찾았습니다. ({track_info.id})'
            return ReturnClassWithResult(_is_error=False, _message=return_class_message, _result=track_info)
        else:
            track_info = TrackInfoUtils.set_track_info(track_id=None, track_title=None, track_artist=None)
            return ReturnClassWithResult(_is_error=True, _message='|> 트랙을 찾지 못했습니다.', _result=track_info)

    def create_playlist(self, playlist_name: str, description: str) -> ReturnClassWithResult:
        default_description = datetime.datetime.now().strftime('(%Y-%m-%d)')
        final_description = self.utils.string_inject((description, default_description), ' ')
        try:
            make_new_playlist = self.parent.user_playlist_create(user=self.SPOTIFY_API_INFO.USER_ID,
                                                                 name=playlist_name,
                                                                 public=True,
                                                                 collaborative=False,
                                                                 description=final_description)
            return ReturnClassWithResult(_is_error=False, _message='✅ 플레이리스트를 만들었습니다.', _result=make_new_playlist['id'])
        except Exception as err:
            print(err)
            return ReturnClassWithResult(_is_error=True, _message='❌ 플레이리스트를 만들지 못했습니다.', _result=None)

    def append_items(self, playlist_id: str, track_items: List[TrackInfo]) -> ReturnClass:
        track_id_items = [track_item.id for track_item in track_items]
        try:
            self.parent.playlist_add_items(playlist_id=playlist_id,
                                           items=track_id_items,
                                           position=None)
            return ReturnClass(_is_error=False, _message='✅ 트랙을 추가했습니다.')
        except Exception as err:
            return ReturnClass(_is_error=True, _message=f'❌ 트랙을 추가하지 못했습니다.\n'
                                                        f'{err}')

    def upload_playlist_thumbnail(self, playlist_id: str) -> ReturnClass:
        # load thumbnail_img
        thumbnail_img_url = 'https://raw.githubusercontent.com/kitae0522/Bugs2Spotify/main/playlist-thumbnail.jpeg'
        thumbnail_img_b64 = base64.b64encode(requests.get(thumbnail_img_url).content).decode('utf-8')

        try:
            self.parent.playlist_upload_cover_image(playlist_id=playlist_id, image_b64=thumbnail_img_b64)
            return ReturnClass(_is_error=False, _message='✅ 플레이리스트 커버 사진을 업로드 했습니다.')
        except Exception as err:
            return ReturnClass(_is_error=True, _message=f'❌ 플레이리스트 커버 사진을 업로드하지 못했습니다.\n'
                                                        f'{err}')


class BugsApp:
    def __init__(self):
        self.utils = Utils()
        self.base_url = 'https://music.bugs.co.kr/musicpd/albumview/'
        self.playlist_url = ''
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    def run(self, playlist_id: str) -> ReturnClassWithResult:
        try:
            with requests.Session() as session:
                self.playlist_url = self.utils.string_inject((self.base_url, playlist_id), '')
                response = session.get(self.playlist_url, headers=self.headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                playlist_header = soup.find('header', {'sectionPadding pgTitle noneLNB'})
                playlist_title = playlist_header.find('h1').text.strip()

                track_list_box = soup.find('div', {'id': f'ESALBUM{self.playlist_url.split("/")[-1]}'})
                track_list_table = track_list_box.find('table', {'class': 'list trackList'})
                track_list_tbody = track_list_table.find('tbody')
                track_list_items = track_list_tbody.find_all('tr')

                track_list_result = [
                    {
                        'title': item.find('th', {'scope': 'row'}).text.strip(),
                        'artist': item.find('td', {'class': 'left'}).find('p', {'class': 'artist'}).a.text.strip()
                    }
                    for item in track_list_items
                ]

                playlist_result = {
                    'title': playlist_title,
                    'items': track_list_result,
                    'count': len(track_list_result)
                }

                return ReturnClassWithResult(_is_error=False,
                                             _message='✅ 벅스 플레이리스트 크롤링에 성공했습니다.',
                                             _result=playlist_result)
        except requests.RequestException as err:
            return ReturnClassWithResult(_is_error=True,
                                         _message=f'❌ 요청 도중 문제가 발생했습니다.\n'
                                                  f'{err}',
                                         _result=None)
        except Exception as err:
            return ReturnClassWithResult(_is_error=True,
                                         _message=f'❌ 예상치 못한 에러가 발생했습니다.\n'
                                                  f'{err}',
                                         _result=None)
