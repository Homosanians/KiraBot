from peewee import *

db = SqliteDatabase('bot.db')


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    user_id = IntegerField(unique=True)


class Post(BaseModel):
    file_name = CharField()


class View(BaseModel):
    post = ForeignKeyField(Post, backref='views')
    user = ForeignKeyField(User, backref='views')


class Assessment(BaseModel):
    post = ForeignKeyField(Post, backref='assessments')
    user = ForeignKeyField(User, backref='assessments')
    positive = BooleanField()


def init():
    db.connect()
    db.create_tables([User, Post, View, Assessment])
    db.close()
