
from database import Database, Raffle, User

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

with database as db:
   db.delete_raffle(14)

