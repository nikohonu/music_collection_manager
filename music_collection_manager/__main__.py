from music_collection_manager.models import Music
from music_collection_manager.models import MusicCollection
from music_collection_manager.utils import Config


def main():
    config = Config()
    music_collection = MusicCollection(config)
    for music in sorted(music_collection.music, key=lambda music: music.scrobbles):
        print(music.artist, music.title, music.album, music.scrobbles)


if __name__ == '__main__':
    main()
