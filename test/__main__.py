import json
import unittest

from core.module import Utils
from core.module import TrackInfo
from core.module import TrackInfoUtils
from core.module import ReturnClass
from core.module import ReturnClassWithResult
from core.module import SpotifyInfo
from core.module import SpotifyApp


class UnitTest(unittest.TestCase):
    with open('config.json', 'r') as config_file:
        utils_class = Utils()
        track_utils_class = TrackInfoUtils()
        spotify_info_class = SpotifyInfo(json.load(config_file))
        spotify_class = SpotifyApp(spotify_info_class)

    def test_string_inject_sep_is_space(self):
        function_result = self.utils_class.string_inject("12345", " ")
        except_result = "1 2 3 4 5"
        self.assertEqual(function_result, except_result)

    def test_string_inject_sep_is_zero_space(self):
        function_result = self.utils_class.string_inject("12345", "")
        except_result = "12345"
        self.assertEqual(function_result, except_result)

    def test_string_inject_sep_is_comma(self):
        function_result = self.utils_class.string_inject("12345", ",")
        except_result = "1,2,3,4,5"
        self.assertEqual(function_result, except_result)

    def test_string_inject_sep_is_none(self):
        function_result = self.utils_class.string_inject("12345")
        except_result = "1 2 3 4 5"
        self.assertEqual(function_result, except_result)

    def test_iter_track_info(self):
        function_result: TrackInfo = self.track_utils_class.set_track_info(
            track_id="1713c022-e525-45c1-ba98-7122879bc74a",
            track_title="animal",
            track_artist="b5ZNs")
        except_result_1, except_result_2, except_result_3 = function_result
        self.assertDictEqual(self.track_utils_class.get_convert_dict(function_result),
                             {'id': except_result_1, 'title': except_result_2, 'artist': except_result_3})

    def test_search_track__found(self):
        sample_track_title = "Stop Breathing"
        sample_track_artist = "Playboi Carti"
        function_result: ReturnClassWithResult = self.spotify_class.search(track=sample_track_title,
                                                                           artist=sample_track_artist)
        self.assertFalse(function_result.is_error)

    def test_search_track__not_found(self):
        sample_track_title = "title:대충한국어제목"
        sample_track_artist = "artist:대충한국인"
        function_result: ReturnClassWithResult = self.spotify_class.search(track=sample_track_title,
                                                                           artist=sample_track_artist)
        self.assertTrue(function_result.is_error)


unittest.main()
