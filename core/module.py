import json
import base64
import random
import datetime
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
    def get_convert_dict(track_info: TrackInfo):
        _track_id, _track_title, _track_artist = track_info
        return {'id': _track_id, 'title': _track_title, 'artist': _track_artist}

    def get_convert_track_info(self, track_info_dict: dict):
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
        self.USER_NAME = config.get('user_name', None)

    def __iter__(self):
        yield self.CLIENT_ID
        yield self.CLIENT_SECRET
        yield self.REDIRECT_URI
        yield self.USER_ID
        yield self.USER_NAME


class SpotifyApp:
    def __init__(self, api_info: SpotifyInfo):
        self.utils = Utils()
        self.scope = ('playlist-modify-public', 'ugc-image-upload')
        self.SPOTIFY_API_INFO = api_info
        self.SPOTIFY_OAUTH = SpotifyOAuth(scope=self.utils.string_inject(self.scope),
                                          client_id=self.SPOTIFY_API_INFO.CLIENT_ID,
                                          client_secret=self.SPOTIFY_API_INFO.CLIENT_SECRET,
                                          redirect_uri=self.SPOTIFY_API_INFO.REDIRECT_URI)
        self.parent = spotipy.Spotify(auth_manager=self.SPOTIFY_OAUTH)
        print(self._get_user_info().message)

    def _get_user_info(self) -> ReturnClassWithResult:
        if self.SPOTIFY_API_INFO.USER_ID and self.SPOTIFY_API_INFO.USER_NAME:
            return self._get_cached_user_info()
        try:
            user_info = self.parent.me()
            return_user_info = ReturnClassWithResult(_is_error=False,
                                                     _message='✅ 외부에서 사용자 ID를 받아오는 데 성공했습니다.',
                                                     _result={'user_id': user_info['id'],
                                                              'user_name': user_info['display_name']})
            self._set_user_info(return_user_info)
            return return_user_info
        except Exception as err:
            return_user_info = ReturnClassWithResult(_is_error=True,
                                                     _message=f'❌ 외부에서 사용자 ID를 받아오는 데 실패했습니다.\n{err}',
                                                     _result={'user_id': None, 'user_name': None})
            self._set_user_info(return_user_info)
            return return_user_info

    def _get_cached_user_info(self) -> ReturnClassWithResult:
        return ReturnClassWithResult(_is_error=False,
                                     _message='✅ 캐시된 파일에서 사용자 ID를 받아오는 데 성공했습니다.',
                                     _result={'user_id': self.SPOTIFY_API_INFO.USER_ID,
                                              'user_name': self.SPOTIFY_API_INFO.USER_NAME})

    def _set_user_info(self, user_info: ReturnClassWithResult):
        get_user_info_err, get_user_info_msg, get_user_info_result = user_info
        self.SPOTIFY_API_INFO.USER_ID = get_user_info_result['user_id']
        self.SPOTIFY_API_INFO.USER_NAME = get_user_info_result['user_name']
        self._save_user_info()

    def _save_user_info(self):
        with open('config.json', 'w') as config_file:
            config_json = {
                'client_id': self.SPOTIFY_API_INFO.CLIENT_ID,
                'client_secret': self.SPOTIFY_API_INFO.CLIENT_SECRET,
                'redirect_uri': self.SPOTIFY_API_INFO.REDIRECT_URI,
                'user_id': self.SPOTIFY_API_INFO.USER_ID,
                'user_name': self.SPOTIFY_API_INFO.USER_NAME
            }
            json.dump(config_json, config_file, indent=2)

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
        final_description = self.utils.string_inject((description, default_description))
        try:
            make_new_playlist = self.parent.user_playlist_create(user=self.SPOTIFY_API_INFO.USER_ID,
                                                                 name=playlist_name,
                                                                 public=True,
                                                                 collaborative=False,
                                                                 description=final_description)
            return ReturnClassWithResult(_is_error=False, _message='✅ 플레이리스트를 만들었습니다.', _result=make_new_playlist['id'])
        except Exception as err:
            return ReturnClassWithResult(_is_error=True, _message=f'❌ 플레이리스트를 만들지 못했습니다.\n{err}', _result=None)

    def append_items(self, playlist_id: str, track_items: List[TrackInfo]) -> ReturnClass:
        track_id_items = [track_item.id for track_item in track_items]
        try:
            self.parent.playlist_add_items(playlist_id=playlist_id,
                                           items=track_id_items,
                                           position=None)
            return ReturnClass(_is_error=False, _message='✅ 트랙을 추가했습니다.')
        except Exception as err:
            return ReturnClass(_is_error=True, _message=f'❌ 트랙을 추가하지 못했습니다.\n{err}')

    def upload_playlist_thumbnail(self, playlist_id: str) -> ReturnClass:
        thumbnail_img_number = random.randint(1, 3)
        # load thumbnail_img
        thumbnail_img_url = f'https://raw.githubusercontent.com/kitae0522/Bugs2Spotify/main/img/' \
                            f'playlist-thumbnail-{thumbnail_img_number}.jpeg'
        thumbnail_img_b64 = base64.b64encode(requests.get(thumbnail_img_url).content).decode('utf-8')

        try:
            self.parent.playlist_upload_cover_image(playlist_id=playlist_id, image_b64=thumbnail_img_b64)
            return ReturnClass(_is_error=False, _message='✅ 플레이리스트 커버 사진을 업로드 했습니다.')
        except Exception as err:
            return ReturnClass(_is_error=True, _message=f'❌ 플레이리스트 커버 사진을 업로드하지 못했습니다.\n{err}')


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
                                         _message=f'❌ 요청 도중 문제가 발생했습니다.\n{err}',
                                         _result=None)
        except Exception as err:
            return ReturnClassWithResult(_is_error=True,
                                         _message=f'❌ 예상치 못한 에러가 발생했습니다.\n{err}',
                                         _result=None)
