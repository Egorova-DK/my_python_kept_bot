from aiogram.utils import executor

from config import TOKEN_API
from database import User, Raffle, Database, Channel
from fsm_dialogs import bot, dp

database = Database()
r=Raffle(
    name = 'sdfsd',
    users_count = 12,
    finish_date = '2023-11-10',
    description = 'we',
    media_url = 'sf qwe',
    id=7
)

u=User(
    raffle_id = 7,
    ticket_number='fwg123',
    telegram_id=23423
)

c=Channel(
    telegram_id=23423
)

with database as db:
   db.delete_channel(23423)
   print(db.get_channels())



