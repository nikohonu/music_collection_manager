from pathlib import Path

from music_collection_manager.utils import Config
from mutagen.flac import FLAC
from mutagen.oggopus import OggOpus
from pylast import Album
from pylast import LastFMNetwork
from pylast import md5
from pylast import PERIOD_12MONTHS


class Music:
    def __init__(self, artist, title, album, length, path):
        self.artist = artist
        self.title = title
        self.album = album
        self.length = length
        self.scrobbles = 0
        self.path = path

    @classmethod
    def from_file(cls, file: Path):
        if file.suffix == '.opus':
            data = OggOpus(file)
        elif file.suffix == '.flac':
            data = FLAC(file)
        artist = data['albumartist'][0] if 'albumartist' in data else data['artist'][0]
        album = data['album'][0]
        title = data['title'][0]
        length = data.info.length
        return cls(artist, title, album, length, file)

    def _fix_path(self, collection_path: Path):
        use_path = collection_path / 'use'
        other_path = collection_path / 'other'
        if str(self.path).startswith(str(other_path)):
            return
        elif str(self.path).startswith(str(use_path)):
            new_path = Path(str(self.path).replace(
                str(use_path), str(other_path)))
        else:
            new_path = Path(str(self.path).replace(
                str(collection_path), str(other_path)))
        new_path.parent.mkdir(parents=True, exist_ok=True)
        self.path.replace(new_path)
        self.path = new_path


class MusicCollection:
    def __init__(self, config: Config):
        self.config = config
        self.music = []
        for extension in ['.opus', '.flac']:
            for file in self.config.collection_path.glob(f'**/*{extension}'):
                music_file = Music.from_file(file)
                music_file._fix_path(self.config.collection_path)
                self.music.append(music_file)
        self._get_data_from_last_fm()
        self._remove_all_sub_folders()

    def _get_data_from_last_fm(self):
        network = LastFMNetwork(api_key=self.config.api_key, api_secret=self.config.api_secret,
                                username=self.config.username, password_hash=md5(self.config.password))
        user = network.get_user(self.config.username)
        data = user.get_top_tracks(PERIOD_12MONTHS)
        for music in data:
            artist = music.item.get_artist().get_name()
            title = music.item.get_title()
            weight = music.weight
            for music_file in [music_file for music_file in self.music if music_file.title == title and music_file.artist == artist]:
                music_file.scrobbles = weight

    def _remove_all_sub_folders(self):
        all_sub_dirs = list(self.config.collection_path.glob('**'))
        all_sub_dirs.reverse()
        for path in [dir for dir in all_sub_dirs if dir.name != '.stfolder']:
            try:
                path.rmdir()
            except:
                pass
