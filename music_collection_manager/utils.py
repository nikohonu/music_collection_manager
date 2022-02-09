from os import abort
from pathlib import Path

from nh_tool.file import save_json
from nh_tools.dirs import get_config_path
from nh_tools.file import open_json


class Config:
    def __init__(self) -> None:
        path = get_config_path() / 'music_collection_manager' / 'config.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        data = open_json(path)
        if not data:
            data['api_key'] = '<LASTFM_API_KEY>'
            data['api_secret'] = '<LASTFM_API_SECRET>'
            data['usernames'] = ['<LASTFM_USERNAME1>', '<LASTFM_USERNAME2>']
            data['password'] = '<LASTFM_PASSWORD>'
            data['collection_path'] = '~/music/'
            print('Fill out the file', path)
            save_json(path, data)
            abort()
        else:
            self.api_key = data['api_key']
            self.api_secret = data['api_secret']
            self.usernames = data['usernames']
            self.password = data['password']
            self.collection_path = Path(data['collection_path']).expanduser()
