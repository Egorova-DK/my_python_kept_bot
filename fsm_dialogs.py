from datetime import datetime

from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from config import TOKEN_API
from keyboards import get_kb_menu, cb2, get_ikb_info, get_ikb_edit, get_ikb_menu, cb, get_ikb_media
from database import Database, Raffle
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

storage = MemoryStorage()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot,
                storage=storage)
db = Database()

kb = InlineKeyboardMarkup()
kb.add(InlineKeyboardButton('Удалить', callback_data='delete_1'))

class ProfileStatesGroup(StatesGroup):
    menu = State()
    raffles = State()
    name = State()
    description_raffle = State()
    count_users = State()
    finish_date = State()
    media_question = State()
    media = State()
    show_raffle = State()
    end = State()


async def on_startup(_):
    print('Бот был успешно запущен')

@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message) -> None:
    await message.answer('Добро пожаловать в чат бот <b>Kept raffle bot</b>! \n'
                         'Бот умеет проводить розыгрыши от компании Kept среди студентов ВУЗов Санкт-Петербурга и самостоятельно выбирать победителей! '
                         '\n\n<b>Команды бота:</b> \n/create_raffle - создание розыгрыша \n/raffles - просмотреть розыгрыши',
                         parse_mode="HTML",
                         reply_markup=get_kb_menu())
    await ProfileStatesGroup.menu.set()

@dp.callback_query_handler(cb2.filter(menu='Menu'), state='*')
async def menu_to_handler(callback: types.CallbackQuery):
    await bot.send_message(callback.from_user.id,
                           'Бот умеет проводить розыгрыши от компании Kept среди студентов ВУЗов Санкт-Петербурга и самостоятельно выбирать победителей! '
                           '\n\n<b>Команды бота:</b> \n/create_raffle - создание розыгрыша \n/raffles - просмотреть розыгрыши',
                           parse_mode="HTML",
                           reply_markup=get_kb_menu())
    await ProfileStatesGroup.menu.set()
    await callback.message.edit_reply_markup()


@dp.message_handler(commands=['raffles'], state='*')
@dp.message_handler(text=['Розыгрыши'], state='*')
async def cmd_show_raffles(message: types.Message) -> None:
    header = 'Список созданных Вами розыгрышей:\n'
    s = ''
    show_keyboard = InlineKeyboardMarkup(row_width=2)
    with db:
        for r in db.get_raffles():
            m = f'Название розыгрыша:<b>{r.name}</b>\n' \
                f'{r.description}\n' \
                f'Количество участников:<b>{r.users_count}</b>\n'
            show_keyboard.add(InlineKeyboardButton(f'{r.name}', callback_data=f'show_raffle_{r.id}'))
            s += m
    await message.answer(header + s, parse_mode='HTML', reply_markup=show_keyboard)
    await ProfileStatesGroup.raffles.set()


@dp.callback_query_handler(state=ProfileStatesGroup.show_raffle, text_startswith='edit_')
async def edit_raffle(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    id = callback.data.split('_')[-1]
    with db:
        r = db.get_raffles(id)
    await bot.send_message(chat_id=callback.from_user.id, text='Что хотите изменить?', parse_mode='HTML',
                           reply_markup=get_ikb_edit(id))



@dp.callback_query_handler(text_startswith='delete_', state='*')
async def delete_raffle(callback: types.CallbackQuery):
    await callback.message.delete()
    id = int(callback.data.split('_')[-1])
    with db:
        db.delete_raffle(id)
    await bot.send_message(chat_id=callback.from_user.id, text='<b>Ваш розыгрыш удален</b>', parse_mode='HTML')



@dp.callback_query_handler(text = 'raffles', state=ProfileStatesGroup.show_raffle)
async def cmd_show_raffles(callback: types.CallbackQuery) -> None:
    await callback.message.delete()
    header = 'Список созданных Вами розыгрышей:\n'
    s = ''
    show_keyboard = InlineKeyboardMarkup(row_width=2)
    with db:
        for r in db.get_raffles():
            m = f'Название розыгрыша:<b>{r.name}</b>\n' \
                f'{r.description}\n' \
                f'Количество участников:<b>{r.users_count}</b>\n'
            show_keyboard.add(InlineKeyboardButton(f'{r.name}', callback_data=f'show_raffle_{r.id}'))
            s += m
    await bot.send_message(chat_id=callback.from_user.id, text=f'{header} + {s}', parse_mode='HTML',
                           reply_markup=show_keyboard)
    await ProfileStatesGroup.raffles.set()


@dp.callback_query_handler(state=ProfileStatesGroup.raffles, text_startswith='show_raffle_')
async def show_raffle(callback: types.CallbackQuery):
    await callback.message.delete()
    id = callback.data.split('_')[-1]
    with db:
        r = db.get_raffles(id)
        m = f'Название розыгрыша:<b>{r.name}</b>\n' \
            f'{r.description}\n' \
            f'Количество участников:<b>{r.users_count}</b>\n'

    await bot.send_message(chat_id=callback.from_user.id, text=m, parse_mode='HTML', reply_markup=get_ikb_info(id))
    await ProfileStatesGroup.show_raffle.set()
#
#
# @dp.callback_query_handler(state=ProfileStatesGroup.show_raffle, text_startswith='run_')
# async def run_raffle(callback: types.CallbackQuery):
#     await callback.message.edit_reply_markup()
#     id = callback.data.split('_')[-1]
#     with db:
#         r = db.get_raffles(id)
#     # Выставляем флаг isActiv
#     await bot.send_message(chat_id=callback.from_user.id, text='<b>Ваш розыгрыш запущен!</b>', parse_mode='HTML')
#
#
#
# @dp.callback_query_handler(state=ProfileStatesGroup.show_raffle, text_startswith='Name_')
# async def edit_name_raffle(callback: types.CallbackQuery):
#     await callback.message.edit_reply_markup()
#     id = callback.data.split('_')[-1]
#     with db:
#         r = db.get_raffles(id)
#     await bot.send_message(chat_id=callback.from_user.id, text='"<b>Введите новое название розыгрыша.</b>?', parse_mode='HTML')

# #
# # @dp.callback_query_handler(state=ProfileStatesGroup.show_raffle, text_startswith='Discription_')
# # async def edit_discription_raffle(callback: types.CallbackQuery):
# #     await callback.message.edit_reply_markup()
# #     id = callback.data.split('_')[-1]
# #     with db:
# #         r = db.get_raffles(id)
# #     await bot.send_message(chat_id=callback.from_user.id, text='"<b>Введите новое описание розыгрыша.</b>?', parse_mode='HTML')
# #     await ProfileStatesGroup.description_raffle.set()
#
#
# # @dp.message_handler(lambda message: not message.text.isdigit() or float(message.text) > 100, state=ProfileStatesGroup.age)
# # async def check_age(message: types.Message):
# #     await message.reply('Введите реальный возраст!')
#

# Создание розыгрыша


@dp.message_handler(commands=['create_raffle'], state='*')
@dp.message_handler(text=['Создать розыгрыш'], state='*')
async def cmd_create_raffle(message: types.Message) -> None:
    await message.answer(text='Сейчас мы создадим розыгрыш', reply_markup=types.ReplyKeyboardRemove())
    await message.answer(
        "<b>Введите название розыгрыша.</b>\nЭто название будет отображаться у пользователя в списке розыгрышей в боте.",
        parse_mode="HTML", reply_markup=get_ikb_menu())
    await ProfileStatesGroup.name.set()


@dp.message_handler(state=ProfileStatesGroup.name)
async def load_name(message: types.Message, state: FSMContext) -> None:
    if message.text.startswith('/'):
        await message.answer(
            "<b>Название не может начинаться с /.</b>\nПопробуйте еще раз",
            parse_mode="HTML")
    else:
        async with state.proxy() as data:
            data['name'] = message.text
        await message.answer(
            '<b>Введите текст подробного описания розыгрыша.</b>\nПодробно опишите условия розыгрыша для ваших подписчиков. После старта розыгрыша введённый текст будет опубликован в привязаном канале.',
            parse_mode="HTML", reply_markup=get_ikb_menu())
        await ProfileStatesGroup.description_raffle.set()


@dp.message_handler(state=ProfileStatesGroup.description_raffle)
async def load_desc(message: types.Message, state: FSMContext) -> None:
    if message.text.startswith('/'):
        await message.answer(
            "<b>Описание не может начинаться с /.</b>\nПопробуйте еще раз",
            parse_mode="HTML")
    else:
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
                           parse_mode="HTML", reply_markup=get_ikb_menu())
    await ProfileStatesGroup.finish_date.set()
    await callback.message.delete()


@dp.callback_query_handler(cb.filter(media='Yes'), state=ProfileStatesGroup.media_question)
async def yes_media_to_handler(callback: types.CallbackQuery):
    await bot.send_message(callback.from_user.id,
                           '<b>Вставьте картинку</b>',
                           parse_mode="HTML")
    await ProfileStatesGroup.media.set()
    await callback.message.edit_reply_markup()


@dp.message_handler(lambda message: not message.photo, state=ProfileStatesGroup.media)
async def check_photo(message: types.Message):
    await message.reply('Это не фотография!')


@dp.message_handler(content_types=['photo'], state=ProfileStatesGroup.media)
async def load_media(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id

    await message.answer(
        '<b>Укажите время заврешения розыгрыша</b>в формате (ЧЧ:ММ ДД.ММ.ГГГГ).\n<b>Например:</b> 12:00 31.12.2023',
        parse_mode="HTML", reply_markup=get_ikb_menu())
    await ProfileStatesGroup.finish_date.set()


def string_to_timestamp(value):
    try:
        if not value.strip():
            return None
        date_time = datetime.strptime(value, '%H:%M %d.%m.%Y')
        return date_time
    except:
        return None


@dp.message_handler(state=ProfileStatesGroup.finish_date)
async def load_finish_date(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['finish_date'] = message.text
        finish_date = string_to_timestamp(data['finish_date'])
        if finish_date is None:
            await message.answer('Некорректная дата. Попробуйте еще раз.', reply_markup=get_ikb_menu())
        else:
            r = Raffle(
                name=data['name'],
                users_count=1000000,
                finish_date=finish_date,
                description=data['description'],
                media_url=data['photo']
            )
            with db:
                db.save_raffle(r)
            await message.answer('Вы успешно создали розыгрыш!', reply_markup=get_kb_menu())
            await ProfileStatesGroup.end.set()



if __name__ == '__main__':
    executor.start_polling(dp,
                           skip_updates=True)
