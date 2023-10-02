from operator import concat

from sqlalchemy import *
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.testing.plugin.plugin_base import logging

import config

Base = declarative_base()


class Raffle(Base):
    __tablename__ = 'raffle'

    name = Column(String)
    users_count = Column(Integer)
    finish_date = Column(DateTime)
    description = Column(String)
    is_active = Column(Boolean, default=False)
    media_url = Column(String, nullable=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    users = relationship("User", back_populates="raffle")

    def __str__(self):
        return concat(self.name, self.users.__str__())


class User(Base):
    __tablename__ = 'users'

    raffle_id = Column(Integer, ForeignKey('raffle.id'))
    raffle = relationship("Raffle", back_populates="users")
    ticket_number = Column(String)
    telegram_id = Column(BigInteger)
    id = Column(Integer, primary_key=True, autoincrement=True)

    def __str__(self):
        return self.ticket_number

class Channel(Base):
    __tablename__ = 'channel'

    telegram_id = Column(BigInteger)
    id = Column(Integer, primary_key=True, autoincrement=True)

    def __str__(self):
        return self.telegram_id

class Database:
    def __init__(self):
        self.engine = create_engine(f"postgresql://{config.user}:{config.password}@"
                                    f"{config.host}:{config.port}/"
                                    f"{config.db_name}")

    def __enter__(self):
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def save_user(self, user: User):
        try:
            self.session.add(user)
            self.session.commit()
        except Exception as ex:
            logging.exception(ex)
            self.session.rollback()

    def save_raffle(self, raffle: Raffle):
        try:
            self.session.add(raffle)
            self.session.commit()
        except Exception as ex:
            logging.exception('There was an exception in save_raffle')
            self.session.rollback()

    def save_channel(self, channel: Channel):
        try:
            self.session.add(channel)
            self.session.commit()
        except Exception as ex:
            logging.exception('There was an exception in save_channel')
            self.session.rollback()

    def update_raffle(self, raffle: Raffle):
        try:
            saved = self.session.query(Raffle).filter(Raffle.id == raffle.id).first()
            if saved:
                saved.media_url = raffle.media_url
                saved.name = raffle.name
                saved.description = raffle.description
                saved.users_count = raffle.users_count
                saved.finish_date = raffle.finish_date
                saved.is_active = raffle.is_active
                self.session.merge(saved)
                self.session.commit()
        except Exception as ex:
            logging.exception('There was an exception in update_raffle')
            self.session.rollback()

    def delete_raffle(self, raffle_id: int):
        try:
            s = self.session.query(Raffle).filter_by(id=raffle_id).one()
            self.session.delete(s)
            self.session.commit()
        except Exception as ex:
            logging.exception('There was an exception in delete_raffle')
            self.session.rollback()

    def delete_channel(self, telegram_id: int):
        try:
            s = self.session.query(Channel).filter_by(telegram_id=telegram_id).one()
            self.session.delete(s)
            self.session.commit()
        except Exception as ex:
            logging.exception('There was an exception in delete_channel')
            self.session.rollback()

    def get_raffles(self, raffle_id=None):
        if not raffle_id:
            try:
                return self.session.query(Raffle).all()
            except Exception as ex:
                logging.exception('There was an exception in get_raffles')
                self.session.rollback()
        else:
            try:
                return self.session.query(Raffle).filter(Raffle.id == raffle_id).one_or_none()
            except Exception as ex:
                logging.exception('There was an exception in get_raffles')
                self.session.rollback()

    def get_channels(self):
        try:
            return self.session.query(Channel).all()
        except Exception as ex:
            logging.exception('There was an exception in get_channel')
            self.session.rollback()
