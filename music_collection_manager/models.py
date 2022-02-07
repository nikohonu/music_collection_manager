from nh_tools.dirs import get_data_path as get_data_path
from peewee import AutoField
from peewee import CompositeKey
from peewee import FloatField
from peewee import IntegerField
from peewee import Model
from peewee import SqliteDatabase
from peewee import TextField


def get_db_path():
    path = get_data_path() / 'music_collection_manager' / 'data.db'
    path.parent.mkdir(parents=False, exist_ok=True)
    return path


class BaseModel(Model):
    class Meta:
        database = SqliteDatabase(get_db_path())


class Music(BaseModel):
    title = TextField()
    artist = TextField()
    scrobbles = IntegerField(null=True)

    class Meta:
        primary_key = CompositeKey('title', 'artist')
