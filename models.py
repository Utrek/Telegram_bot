
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship,sessionmaker

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'

    id = sq.Column(sq.Integer, primary_key=True)
    user_name = sq.Column(sq.String(length=40), unique=True)

    def __str__(self):
        return f'{self.user_name}, {self.id}'
    
class Words(Base):
    __tablename__ = 'words'
     
    id = id = sq.Column(sq.Integer, primary_key=True)
    english_word = sq.Column(sq.String(length=40))
    russian_word = sq.Column(sq.String(length=40))
     
    def __str__(self):
        return f'Words: {self.english_word},{self.russian_word}'

class Added_words(Base):
    __tablename__ = 'added_words'
    
    id = sq.Column(sq.Integer, primary_key=True)
    english_word = sq.Column(sq.String(length=40))
    russian_word = sq.Column(sq.String(length=40))
    user_id = sq.Column(sq.Integer, sq.ForeignKey('users.id'))
    
    def __str__(self):
        return f'Added_words: {self.english_word},{self.russian_word}, {self.user_id}'
    
    user = relationship(Users, backref="added_words")

class Deleted_words(Base):
    __tablename__ = 'deleted_words'

    id = sq.Column(sq.Integer, primary_key=True)
    english_word = sq.Column(sq.String(length=40))
    russian_word = sq.Column(sq.String(length=40))
    user_id = sq.Column(sq.Integer, sq.ForeignKey('users.id'))
    
    def __str__(self):
        return f'Deleted_words: {self.russian_word}, {self.english_word}, {self.user_id}'
    
    user = relationship(Users, backref="deleted_words")


def create_tables(engine):
     #Base.metadata.drop_all(engine)
     Base.metadata.create_all(engine)
     



