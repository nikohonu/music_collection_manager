from pathlib import Path
from random import choice

from music_collection_manager.utils import Config
from mutagen.flac import FLAC
from mutagen.oggopus import OggOpus
from pylast import LastFMNetwork
from pylast import md5
from pylast import PERIOD_12MONTHS
from pylast import PERIOD_OVERALL


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
        use_path = collection_path / 'used'
        other_path = collection_path / 'other'
        if str(self.path).startswith(str(other_path)):
            return
        elif str(self.path).startswith(str(use_path)):
            new_path = Path(str(self.path).replace(
                str(use_path), str(other_path)))
        else:
            new_path = Path(str(self.path).replace(
                str(collection_path), str(other_path)))
        self.move(new_path)

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
        self.music = []
        self.used = set()
        for extension in ['.opus', '.flac']:
            for file in self.config.collection_path.glob(f'**/*{extension}'):
                music_file = Music.from_file(file)
                music_file._fix_path(self.config.collection_path)
                self.music.append(music_file)
        self._get_data_from_last_fm()
        self.music = sorted(
            self.music, key=lambda music: music.scrobbles, reverse=True)
        self.create_top_playlist(32)
        self.create_random_playlist(32)
        self.move_music()
        self._remove_all_sub_folders()

    def _get_data_from_last_fm(self):
        music_all = {}
        music12 = {}
        network = LastFMNetwork(api_key=self.config.api_key, api_secret=self.config.api_secret,
                                username=self.config.usernames[0], password_hash=md5(self.config.password))
        users = [network.get_user(username)
                 for username in self.config.usernames]
        # PERIOD_OVERALL
        for user in users:
            data = user.get_top_tracks(PERIOD_OVERALL)
            for music in data:
                artist: str = music.item.get_artist().get_name()
                title: str = music.item.get_title()
                weight: int = music.weight
                if (artist, title) not in music:
                    music_all[(artist, title)] = weight
                else:
                    music_all[(artist, title)] += weight
        # PERIOD_12MONTHS
        for user in users:
            data = user.get_top_tracks(PERIOD_12MONTHS)
            for music in data:
                artist: str = music.item.get_artist().get_name()
                title: str = music.item.get_title()
                weight: int = music.weight
                if (artist, title) not in music:
                    music12[(artist, title)] = weight
                else:
                    music12[(artist, title)] += weight
        # sum
        for m in music_all:
            if music_all[m] > 100:
                music_all[m] = music12[m] if m in music12 else 0
            for music_file in [music_file for music_file in self.music if music_file.title == m[1] and music_file.artist == m[0]]:
                music_file.scrobbles = music_all[m]

    def _remove_all_sub_folders(self):
        all_sub_dirs = list(self.config.collection_path.glob('**'))
        all_sub_dirs.reverse()
        for path in [dir for dir in all_sub_dirs if dir.name != '.stfolder']:
            try:
                path.rmdir()
            except:
                pass

    def print_music(self, music: set):
        for m in music:
            print(m.artist, '-', m.title, m.scrobbles)

    def create_top_playlist(self, count=33):
        filterd_music = [m for m in self.music[:count*2] if m.scrobbles <= 100]
        if len(filterd_music) < count:
            return filterd_music
        music = set(filterd_music[:count])
        print('top')
        self.print_music(music)
        self.used.update(music)
        self.save_playlist('top', music)

    def create_random_playlist(self, count=33):
        music = set()
        if len(self.music) < count*4:
            while len(music) < min(count, len(self.music)):
                music.add(choice(self.music))
            return music
        min_scrobbles = min([m.scrobbles for m in self.music])
        first_part = [m for m in self.music if m.scrobbles == min_scrobbles]
        second_part = [m for m in self.music[:count*2] if m.scrobbles <= 100]
        third_part = [m for m in self.music[count*2:]
                      if m.scrobbles != min_scrobbles]
        while min(len(music), len(first_part)) < count/3:
            music.add(choice(first_part))
        while min(len(music), len(second_part)) < (count/3)*2:
            music.add(choice(second_part))
        while min(len(music), len(third_part)) < count:
            music.add(choice(third_part))
        print('random')
        self.print_music(music)
        self.used.update(music)
        self.save_playlist('random', music)

    def save_playlist(self, name: str, music: set):
        playlist = ''
        for m in music:
            playlist += str(m.path).replace(str(self.config.collection_path / 'other'),
                                            str('used')) + '\n'
        (self.config.collection_path / f'{name}.m3u').write_text(playlist)

    def move_music(self):
        for music in self.used:
            new_path = Path(str(music.path).replace(str(self.config.collection_path / 'other'),
                                                    str(self.config.collection_path / 'used')))
            music.move(new_path)
