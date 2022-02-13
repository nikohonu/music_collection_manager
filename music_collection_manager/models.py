from pathlib import Path
from random import choice, randrange

from music_collection_manager.utils import Config
from mutagen.flac import FLAC
from mutagen.oggopus import OggOpus
from pylast import LastFMNetwork, User
from pylast import md5
from pylast import PERIOD_12MONTHS
from pylast import PERIOD_OVERALL


class Music:
    def __init__(self, artist, title, album, length, path):
        self.artist = artist
        self.title = title
        self.album = album
        self.length = length
        self.overall_scrobbles = 0
        self.last_year_scrobbles = 0
        self.path = path

    @classmethod
    def from_file(cls, file: Path):
        if file.suffix == '.opus':
            data = OggOpus(file)
        elif file.suffix == '.flac':
            data = FLAC(file)
        # artist = data['albumartist'][0] if 'albumartist' in data else data['artist'][0]

        artist = data['artist'][0] if 'artist' in data else data['albumartist'][0]
        album = data['album'][0]
        title = data['title'][0]
        length = data.info.length
        return cls(artist, title, album, length, file)

    def move(self, new_path: Path):
        new_path.parent.mkdir(parents=True, exist_ok=True)
        self.path.replace(new_path)
        self.path = new_path

    def __eq__(self, other) -> bool:
        if self.artist == other.artist and \
                self.title == other.title and \
                self.album == other.album:
            return True
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.artist + self.title + self.album)


class MusicCollection:
    def __init__(self, config: Config):
        self.config = config
        self._initial_organization()
        self.music = self._load_music()
        self.used = set()
        self._load_scrobbles()
        self._generate_classic_playlist()
        self._generate_top_playlist()
        self._generate_today_playlist()
        self._move_music()
        self._remove_empty_dirs()

    def _get_music_files(self):
        files = []
        for extension in ['flac', 'opus']:
            for file in self.config.collection_path.glob(f'**/*.{extension}'):
                files.append(file)
        return files

    def _initial_organization(self):
        for file in self._get_music_files():
            if not str(file).startswith(str(self.config.collection_path / 'used')) and \
                    not str(file).startswith(str(self.config.collection_path / 'other')):
                new_file = Path(str(file).replace(str(self.config.collection_path),
                                                  str(self.config.collection_path / 'other')))
                new_file.parent.mkdir(parents=True, exist_ok=True)
                file.replace(new_file)

    def _load_music(self):
        music = []
        for file in self._get_music_files():
            music.append(Music.from_file(file))
        return music

    def _remove_empty_dirs(self):
        dirs = list(self.config.collection_path.glob('**'))
        dirs.reverse()
        for path in [dir for dir in dirs if dir.name != '.stfolder']:
            try:
                path.rmdir()
            except:
                pass

    def _load_scrobbles(self):
        def _load_data(user: User, period: str):
            tracks = user.get_top_tracks(period)
            data = {}
            for track in tracks:
                artist: str = track.item.get_artist().get_name()
                title: str = track.item.get_title()
                weight: int = track.weight
                if artist not in data:
                    data[artist] = {}
                data[artist][title] = weight
            return data

        def _get_data(data: dict, artist: str, title: str):
            if artist in data and title in data[artist]:
                return data[artist][title]
            else:
                return 0

        network = LastFMNetwork(api_key=self.config.api_key, api_secret=self.config.api_secret,
                                username=self.config.username, password_hash=md5(self.config.password))
        user = network.get_user(self.config.username)
        overall_data = _load_data(user, PERIOD_OVERALL)
        last_year_data = _load_data(user, PERIOD_12MONTHS)
        for music in self.music:
            music.overall_scrobbles = _get_data(
                overall_data, music.artist, music.title)
            music.last_year_scrobbles = _get_data(
                last_year_data, music.artist, music.title)

    def _print_music(self, music: set):
        for m in music:
            print(m.artist, '-', m.title, m.last_year_scrobbles)

    def _generate_top_playlist(self, count=33):
        music = sorted(
            self.music, key=lambda music: music.last_year_scrobbles, reverse=True)
        count = len(music) if count > len(music) else count
        music = set(music[:count])
        self._save_playlist('top', music)

    def _generate_classic_playlist(self, count=33):
        music = sorted(
            self.music, key=lambda music: music.overall_scrobbles, reverse=True)
        count = len(music) if count > len(music) else count
        music = set(music[:count])
        self._save_playlist('classic', music)

    def _generate_today_playlist(self, count=33):
        music = set()
        music_collection = [
            m for m in self.music if m.last_year_scrobbles <= 100]
        if len(music_collection) < count*4:
            while len(music) < min(count, len(music_collection)):
                music.add(choice(music_collection))
            self._save_playlist('today', music)
            return
        min_scrobbles = min([m.last_year_scrobbles for m in music_collection])
        first_part = [m for m in music_collection[:count*2]
                      if m.last_year_scrobbles != min_scrobbles]
        second_part = [m for m in music_collection[count*2:]
                       if m.last_year_scrobbles != min_scrobbles]
        third_part = [
            m for m in music_collection if m.last_year_scrobbles == min_scrobbles]

        need = round(count / 3)
        while first_part and len(music) < need:
            music.add(first_part.pop(randrange(len(first_part))))
        need = round(count / 3 * 2)
        while second_part and len(music) < need:
            music.add(second_part.pop(randrange(len(second_part))))
        need = count
        while third_part and len(music) < need:
            music.add(third_part.pop(randrange(len(third_part))))
        self._save_playlist('today', music)

    def _save_playlist(self, name: str, music: set):
        print(name)
        self._print_music(music)
        self.used.update(music)
        playlist = ''
        for m in music:
            if str(m.path).startswith(str(self.config.collection_path / 'other')):
                m.move(Path(str(m.path).replace(
                    str(self.config.collection_path / 'other'),
                    str(self.config.collection_path / 'used')
                )))
            playlist += str(m.path).replace(
                str(self.config.collection_path) + '/', '') + '\n'
        (self.config.collection_path / f'{name}.m3u').write_text(playlist)

    def _move_music(self):
        for music in self.music:
            if music not in self.used:
                new_path = Path(str(music.path).replace(str(self.config.collection_path / 'used'),
                                                        str(self.config.collection_path / 'other')))
                music.move(new_path)
