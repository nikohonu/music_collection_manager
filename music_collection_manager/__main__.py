from music_collection_manager.models import MusicCollection
from music_collection_manager.utils import Config


def main():
    config = Config()
    music_collection = MusicCollection(config)


if __name__ == '__main__':
    main()
