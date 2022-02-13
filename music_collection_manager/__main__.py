from music_collection_manager.models import MusicCollection
from music_collection_manager.utils import Config


def main():
    MusicCollection(Config())


if __name__ == '__main__':
    main()
