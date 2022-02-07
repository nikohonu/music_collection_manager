from os import abort
from pathlib import Path

from music_collection_manager.models import Music
from nh_tool.file import save_json
from nh_tools.dirs import get_config_path
from nh_tools.file import open_json
from pylast import Album
from pylast import LastFMNetwork
from pylast import md5
from pylast import PERIOD_12MONTHS


class Config:
    def __init__(self, data) -> None:
        self.api_key = data['api_key']
        self.api_secret = data['api_secret']
        self.username = data['username']
        self.password = data['password']
        self.music_arcive_path = Path(data['music_arcive_path'])
        self.music_path = Path(data['music_path'])


def load_config():
    path = get_config_path() / 'music_collection_manager' / 'config.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    data = open_json(path)
    if not data:
        data['api_key'] = '<LASTFM_API_KEY>'
        data['api_secret'] = '<LASTFM_API_SECRET>'
        data['username'] = '<LASTFM_USERNAME>'
        data['password'] = '<LASTFM_PASSWORD>'
        data['music_arcive_path'] = '~/archive/music/'
        data['music_path'] = '~/music/'
        print('Fill out the file', path)
        save_json(path, data)
        abort()
    else:
        return Config(data)


def update_database(config: Config, pretend=False):
    if not pretend:
        if not Music.table_exists():
            Music.create_table()
        network = LastFMNetwork(api_key=config.api_key, api_secret=config.api_secret,
                                username=config.username, password_hash=md5(config.password))
        user = network.get_user(config.username)
        data = user.get_top_tracks(PERIOD_12MONTHS)
        for track in data:
            artist = track.item.get_artist().get_name()
            title = track.item.get_title()
            weight = track.weight
            music, _ = Music.get_or_create(title=title, artist=artist)
            music.scrobbles = weight
            music.save()


def main():
    config = load_config()
    update_database(config, pretend=True)


if __name__ == '__main__':
    main()
