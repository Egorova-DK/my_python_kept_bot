import datetime
from datetime import datetime, date

from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from config import TOKEN_API
from keyboards import get_kb_menu, get_ikb_media, cb
from database import Database, Raffle, User

storage = MemoryStorage()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot,
                storage=storage)
db = Database()


class ProfileStatesGroup(StatesGroup):
    menu = State()
    raffles = State()
    name = State()
    description_raffle = State()
    count_users = State()
    finish_date = State()
    media_question = State()
    media = State()
    confirm = State()


async def on_startup(_):
    print('Бот был успешно запущен')


# def get_cancel_kb() -> ReplyKeyboardMarkup:
#     kb = ReplyKeyboardMarkup(resize_keyboard=True)
#     kb.add(KeyboardButton('/cancel'))
#
#     return kb


# @dp.message_handler(commands=['cancel'], state='*')
# async def cmd_cancel(message: types.Message, state: FSMContext):
#     if state is None:
#         return
#
#     await state.finish()
#     await message.reply('Вы прервали создание анкеты!',
#                         reply_markup=get_kb())

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message) -> None:
    await message.answer('Добро пожаловать в чат бот <b>Kept raffle bot</b>! \n'
                         'Бот умеет проводить розыгрыши от компании Kept среди студентов ВУЗов Санкт-Петербурга и самостоятельно выбирать победителей! '
                         '\n\n<b>Команды бота:</b> \n/create_raffle - создание розыгрыша \n/raffles - просмотреть розыгрыши',
                         parse_mode="HTML",
                         reply_markup=get_kb_menu())


@dp.message_handler(commands=['create_raffle'])
@dp.message_handler(text=['Создать розыгрыш'])
async def cmd_create_raffle(message: types.Message) -> None:
    await message.answer(
        "<b>Введите название розыгрыша.</b>\nЭто название будет отображаться у пользователя в списке розыгрышей в боте.",
        parse_mode="HTML")
    await ProfileStatesGroup.name.set()


@dp.message_handler(state=ProfileStatesGroup.name)
async def load_name(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer(
        '<b>Введите текст подробного описания розыгрыша.</b>\nПодробно опишите условия розыгрыша для ваших подписчиков. После старта розыгрыша введённый текст будет опубликован в привязаном канале.',
        parse_mode="HTML")
    await ProfileStatesGroup.description_raffle.set()


@dp.message_handler(state=ProfileStatesGroup.description_raffle)
async def load_desc(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['description'] = message.text
    await message.answer("Хотите добавить картинку/gif/видео для розыгрыша?",
                         reply_markup=get_ikb_media())
    await ProfileStatesGroup.media_question.set()


@dp.callback_query_handler(cb.filter(media='No'), state=ProfileStatesGroup.media_question)
async def no_media_to_handler(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['photo'] = None
    await bot.send_message(callback.from_user.id,
                           '<b>Укажите время заврешения розыгрыша</b>в формате (ЧЧ:ММ ДД.ММ.ГГГГ).\n<b>Например:</b> 12:00 31.12.2023',
                           parse_mode="HTML")
    await ProfileStatesGroup.finish_date.set()


@dp.callback_query_handler(cb.filter(media='Yes'), state=ProfileStatesGroup.media_question)
async def yes_media_to_handler(callback: types.CallbackQuery):
    await bot.send_message(callback.from_user.id,
                           '<b>Вставьте картинку</b>',
                           parse_mode="HTML")
    await ProfileStatesGroup.media.set()


@dp.message_handler(lambda message: not message.photo, state=ProfileStatesGroup.media)
async def check_photo(message: types.Message):
    await message.reply('Это не фотография!')


@dp.message_handler(content_types=['photo'], state=ProfileStatesGroup.media)
async def load_media(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id

    await message.answer(
        '<b>Укажите время заврешения розыгрыша</b>в формате (ЧЧ:ММ ДД.ММ.ГГГГ).\n<b>Например:</b> 12:00 31.12.2023',
        parse_mode="HTML")
    await ProfileStatesGroup.finish_date.set()


def convert_to_datetime(date: str) -> date:
    return datetime.datetime.strptime(date, 'HH:MM dd.mm.YYYY').date()


@dp.message_handler(state=ProfileStatesGroup.finish_date)
async def load_finish_date(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['finish_date'] = message.text
    r = Raffle(
        name=data['name'],
        users_count=1000000,
        finish_date=convert_to_datetime(data['finish_date']),
        description=data['description'],
        media_url=data['photo']
    )
    with db:
        db.save_raffle(r)
    await message.answer('Вы успешно создали розыгрыш!')
    await cmd_start(message)


@dp.message_handler(commands=['raffles'])
@dp.message_handler(text=['Розыгрыши'])
async def cmd_create_raffle(message: types.Message) -> None:
    header = 'Список созданных Вами розыгрышей:\n'
    s = ''
    show_keyboard = InlineKetboardMarkup()
    with db:
        for r in db.get_raffles():
            m = f'Название розыгрыша:<b>{r.name}</b>\n' \
                f'{r.description}\n' \
                f'Количество участников:<b>{r.users_count}</b>\n'
            show_keyboard.add(Inlnin)
            s += m
    await message.answer(header + s, parse_mode='HTML', reply_markup=show_keyboard)


# @dp.message_handler(lambda message: not message.photo, state=ProfileStatesGroup.photo)
# async def check_photo(message: types.Message):
#     await message.reply('Это не фотография!')

#
#
# @dp.message_handler(lambda message: not message.text.isdigit() or float(message.text) > 100, state=ProfileStatesGroup.age)
# async def check_age(message: types.Message):
#     await message.reply('Введите реальный возраст!')
#
#
# @dp.message_handler(state=ProfileStatesGroup.name)
# async def load_name(message: types.Message, state: FSMContext) -> None:
#     async with state.proxy() as data:
#         data['name'] = message.text
#
#     await message.reply('Сколько тебе лет?')
#     await ProfileStatesGroup.next()
#
#
# @dp.message_handler(state=ProfileStatesGroup.age)
# async def load_age(message: types.Message, state: FSMContext) -> None:
#     async with state.proxy() as data:
#         data['age'] = message.text
#
#     await message.reply('А теперь расскажи немного о себе!')
#     await ProfileStatesGroup.next()
#
#
# @dp.message_handler(state=ProfileStatesGroup.description)
# async def load_desc(message: types.Message, state: FSMContext) -> None:
#     async with state.proxy() as data:
#         data['description'] = message.text
#         await bot.send_photo(chat_id=message.from_user.id,
#                              photo=data['photo'],
#                              caption=f"{data['name']}, {data['age']}\n{data['description']}")
#
#     await message.reply('Ваша акнета успешно создана!')
#     await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp,
                           skip_updates=True)
