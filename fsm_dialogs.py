import random
from datetime import datetime
from itertools import product

from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ChatMemberUpdated, ChatMemberStatus, InputMediaPhoto
from aiogram.types import InputFile

from config import TOKEN_API, ID_CHANNEL
from keyboards import get_kb_menu, cb2, get_ikb_info, get_ikb_edit, get_ikb_menu, cb, get_ikb_media
from database import Database, Raffle, Channel, User
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
    edit_name = State()
    edit_description = State()
    edit_finish_date = State()
    edit_place = State()
    engage = State()
    place = State()


async def on_startup(_):
    print('Бот был успешно запущен')


def notify_raffle(raffle):
    ...


@dp.my_chat_member_handler()
async def on_add_to_chat(update: types.ChatMemberUpdated):
    if update.old_chat_member.status in [ChatMemberStatus.KICKED, ChatMemberStatus.LEFT, ChatMemberStatus.RESTRICTED] \
            and update.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR and update.chat.id == ID_CHANNEL:
        db.save_channel(channel=Channel(update.chat.id))
    elif update.old_chat_member.status == ChatMemberStatus.ADMINISTRATOR \
            and update.new_chat_member.status in [ChatMemberStatus.KICKED, ChatMemberStatus.LEFT,
                                                  ChatMemberStatus.RESTRICTED]:
        db.delete_channel(telegram_id=update.chat.id)


@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message) -> None:
    member = await bot.get_chat_member(ID_CHANNEL, message.from_user.id)
    if member.is_chat_admin():
        await message.answer('Добро пожаловать в чат бот <b>Kept raffle bot</b>! \n'
                             'Бот умеет проводить розыгрыши от компании Kept среди студентов ВУЗов Санкт-Петербурга и самостоятельно выбирать победителей! '
                             '\n\n<b>Команды бота:</b> \n/create_raffle - создание розыгрыша \n/raffles - просмотреть розыгрыши',
                             parse_mode="HTML",
                             reply_markup=get_kb_menu())
        await ProfileStatesGroup.menu.set()
    else:
        with db:
            r = db.get_first_raffle()
            if r:
                users = db.get_user_by_raffle_id(r.id)
                for user in users:
                    if user.telegram_id == message.from_user.id:
                        await message.answer('Вы уже участвуете в розыгрыше!')
                        return
                await ProfileStatesGroup.engage.set()
                if r.media_url:
                    await bot.send_photo(chat_id=message.from_user.id,
                                         photo=r.media_url,
                                         caption=f'{r.name}\n{r.description}\nДата подведения итогов:{r.finish_date}',
                                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton('Участвовать', callback_data=f'Engage_{r.id}')],
                    ]))
                else:
                    await bot.send_message(chat_id=message.from_user.id, text=f'<b>{r.name}</b>\n{r.description}\n<b>Дата подведения итогов:</b>{r.finish_date}',
                                           parse_mode='HTML',
                                           reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton('Участвовать', callback_data=f'Engage_{r.id}')],
                    ]))
            else:
                await message.answer('Пока нет запущенных розыгрышей')


uniq_id = set()
for code in product(range(10), repeat=5):
    uniq_id.add(''.join(map(str, code)))


@dp.callback_query_handler(state=ProfileStatesGroup.engage, text_startswith='Engage_')
async def cmd_try_to_engage(callback: types.CallbackQuery) -> None:
    raffle_id = callback.data.split('_')[-1]
    member = await bot.get_chat_member(ID_CHANNEL, callback.from_user.id)
    if member.is_chat_member():
        with db:
            u = User(
                    raffle_id=raffle_id,
                    ticket_number=uniq_id.pop(),
                    telegram_id=callback.from_user.id,
                )
            db.save_user(u)
            await bot.send_message(chat_id=callback.from_user.id, text=f'Вы успешно зарегистрировались на розыгрыш!\nВаш уникальный код: <b>{u.ticket_number}</b>',
                                   parse_mode='HTML')
            await callback.message.delete()
    else:
        link = await bot.create_chat_invite_link(ID_CHANNEL)
        await callback.answer(cache_time=1)
        await bot.send_message(
            chat_id=callback.from_user.id,
            text=f'Сначала вступите в канал\n{link.invite_link}',
            parse_mode='HTML',
        )


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
    await show_raffles(message.from_user.id)
    await ProfileStatesGroup.raffles.set()


@dp.callback_query_handler(state=ProfileStatesGroup.show_raffle, text_startswith='edit_')
async def edit_raffle(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    id = callback.data.split('_')[-1]
    await bot.send_message(chat_id=callback.from_user.id, text='Что хотите изменить?', parse_mode='HTML',
                           reply_markup=get_ikb_edit(id))


@dp.callback_query_handler(text_startswith='delete_', state=ProfileStatesGroup.show_raffle)
async def delete_raffle(callback: types.CallbackQuery):
    await callback.message.delete()
    id = int(callback.data.split('_')[-1])
    with db:
        db.delete_raffle(id)
    await bot.send_message(chat_id=callback.from_user.id, text='<b>Ваш розыгрыш удален</b>', parse_mode='HTML')
    await show_raffles(chat_id=callback.from_user.id)


@dp.callback_query_handler(text='raffles', state=ProfileStatesGroup.show_raffle)
async def cmd_show_raffles(callback: types.CallbackQuery) -> None:
    await callback.message.delete()
    await show_raffles(chat_id=callback.from_user.id)
    await ProfileStatesGroup.raffles.set()


@dp.callback_query_handler(state=ProfileStatesGroup.raffles, text_startswith='show_raffle_')
async def show_raffle(callback: types.CallbackQuery):
    await callback.message.delete()
    id = callback.data.split('_')[-1]
    await show_raffle_id(id, chat_id=callback.from_user.id)


@dp.callback_query_handler(state=ProfileStatesGroup.show_raffle, text_startswith='run_')
async def run_raffle(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    await callback.message.delete()
    id = callback.data.split('_')[-1]
    with db:
        r = db.get_raffles(id)
        if r.finish_date <= datetime.now():
            await bot.send_message(chat_id=callback.from_user.id,
                                   text='<b>Нельзя запустить розыгрыш.</b> Время проведения вышло', parse_mode='HTML')
        else:
            r.is_active = True
            db.update_raffle(r)
            await bot.send_message(chat_id=callback.from_user.id, text='<b>Ваш розыгрыш запущен!</b>',
                                   parse_mode='HTML')
        await show_raffle_id(id, chat_id=callback.from_user.id)


@dp.callback_query_handler(state=ProfileStatesGroup.show_raffle, text_startswith='complete_')
async def complete_raffle(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    id = callback.data.split('_')[-1]
    with db:
        r = db.get_raffles(id)
        r.is_active = False
        r.finish_date = datetime.now()
        db.update_raffle(r)
        await finish_raffle(int(id))
        await bot.send_message(chat_id=callback.from_user.id, text='Розыгрыш завершен!')


async def finish_raffle(raffle_id: int):
    with db:
        r = db.get_raffles(raffle_id)
        users = db.get_user_by_raffle_id(raffle_id)
        winner = users[random.randint(0, len(users) - 1)]
        for user in users:
            if user == winner:
                await bot.send_message(chat_id=user.telegram_id, text=f'Ты победил в розыгрыше {r.name}!')
                await bot.send_message(chat_id=user.telegram_id, text=f'Забрать приз ты сможешь по адресу {r.place_of_prize}')
            else:
                await bot.send_message(chat_id=user.telegram_id, text=f'Ты проиграл в розыгрыше {r.name}(!')
    admins = await bot.get_chat_administrators(ID_CHANNEL)
    for admin in admins:
        button_url = f'tg://openmessage?user_id={winner.telegram_id}'
        await bot.send_message(chat_id=admin.user.id, text=f'В розыгрыше <b>{r.name}</b> определен победитель. '
                                                           f'Нажми на кнопку, чтобы связаться с ним',
                               parse_mode='HTML', reply_markup=InlineKeyboardMarkup([InlineKeyboardButton(text="Победитель", url=button_url)]))

@dp.callback_query_handler(state=ProfileStatesGroup.show_raffle, text_startswith='Place_')
async def show_edit_place_raffle(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    id = callback.data.split('_')[-1]
    async with state.proxy() as data:
        data['edit_place_id'] = id
    await bot.send_message(chat_id=callback.from_user.id,
                           text='<b>Введите новую информацию о месте и времени получения подарка</b>',
                           parse_mode='HTML')
    await ProfileStatesGroup.edit_place.set()


@dp.message_handler(state=ProfileStatesGroup.edit_place)
async def edit_place_raffle(message: types.Message, state: FSMContext):
    if message.text.startswith('/'):
        await message.answer(
            "<b>Информация о месте получения подарка не может начинаться с /.</b>\nПопробуйте еще раз",
            parse_mode="HTML")
    else:
        async with state.proxy() as data:
            id = data['edit_place_id']
            data['edit_place_id'] = None
        with db:
            r = db.get_raffles(id)
            r.place_of_prize = message.text
            db.update_raffle(r)
        await show_raffle_id(id, chat_id=message.from_user.id)


@dp.callback_query_handler(state=ProfileStatesGroup.show_raffle, text_startswith='Name_')
async def show_edit_name_raffle(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    id = callback.data.split('_')[-1]
    async with state.proxy() as data:
        data['edit_name_id'] = id
    await bot.send_message(chat_id=callback.from_user.id, text='<b>Введите новое название розыгрыша.</b>',
                           parse_mode='HTML')
    await ProfileStatesGroup.edit_name.set()


@dp.message_handler(state=ProfileStatesGroup.edit_name)
async def edit_name_raffle(message: types.Message, state: FSMContext):
    if message.text.startswith('/'):
        await message.answer(
            "<b>Название не может начинаться с /.</b>\nПопробуйте еще раз",
            parse_mode="HTML")
    else:
        async with state.proxy() as data:
            id = data['edit_name_id']
            data['edit_name_id'] = None
        with db:
            r = db.get_raffles(id)
            r.name = message.text
            db.update_raffle(r)
        await show_raffle_id(id, chat_id=message.from_user.id)


@dp.callback_query_handler(state=ProfileStatesGroup.show_raffle, text_startswith='Discription_')
async def show_edit_discription_raffle(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    id = callback.data.split('_')[-1]
    async with state.proxy() as data:
        data['edit_discription_id'] = id
    await bot.send_message(chat_id=callback.from_user.id, text='<b>Введите новое описание розыгрыша.</b>',
                           parse_mode='HTML')
    await ProfileStatesGroup.edit_description.set()


@dp.message_handler(state=ProfileStatesGroup.edit_description)
async def edit_description_raffle(message: types.Message, state: FSMContext):
    if message.text.startswith('/'):
        await message.answer(
            "<b>Описание не может начинаться с /.</b>\nПопробуйте еще раз",
            parse_mode="HTML")
    else:
        async with state.proxy() as data:
            id = data['edit_discription_id']
            data['edit_discription_id'] = None
        with db:
            r = db.get_raffles(id)
            r.description = message.text
            db.update_raffle(r)
        await show_raffle_id(id, chat_id=message.from_user.id)


@dp.callback_query_handler(state=ProfileStatesGroup.show_raffle, text_startswith='Finish_date_')
async def show_edit_finish_date_raffle(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    id = callback.data.split('_')[-1]
    async with state.proxy() as data:
        data['edit_finish_date_id'] = id
    await bot.send_message(chat_id=callback.from_user.id,
                           text='<b>Введите новую дату окончания розыгрыша</b> в формате (ЧЧ:ММ ДД.ММ.ГГГГ). <b>Например</b>: 12:00 31.12.2023.',
                           parse_mode='HTML')
    await ProfileStatesGroup.edit_finish_date.set()


@dp.message_handler(state=ProfileStatesGroup.edit_finish_date)
async def edit_finish_date_raffle(message: types.Message, state: FSMContext):
    finish_date = string_to_timestamp(message.text)
    if finish_date is None:
        await message.answer('Некорректная дата. Попробуйте еще раз.')
    else:
        async with state.proxy() as data:
            id = data['edit_finish_date_id']
            data['edit_finish_date_id'] = None
        with db:
            r = db.get_raffles(id)
            r.finish_date = finish_date
            db.update_raffle(r)
        await show_raffle_id(id, chat_id=message.from_user.id)


async def show_raffle_id(id, chat_id):
    with db:
        r = db.get_raffles(id)
        if r.finish_date <= datetime.now():
            status = 'Завершен'
        elif r.is_active:
            status = 'Запущен'
        else:
            status = 'Не запущен'
        if r.media_url:
            await bot.send_photo(chat_id=chat_id,
                                 photo=r.media_url,
                                 caption=f'<b>{r.name}</b>\n' \
                f'{r.description}\n' \
                f'<b>Количество участников:</b> {r.users_count}\n' \
                f'<b>Дата окончания:</b> {r.finish_date}\n' \
                f'<b>Статус:</b> {status}\n' \
                f'<b>Место получения подарка:</b> {r.place_of_prize}',
                                 parse_mode='HTML',
                                 reply_markup=get_ikb_info(id, r.is_active))
        else:
            m = f'<b>{r.name}</b>\n' \
                f'{r.description}\n' \
                f'<b>Количество участников:</b> {r.users_count}\n' \
                f'<b>Дата окончания:</b> {r.finish_date}\n' \
                f'<b>Статус:</b> {status}\n' \
                f'<b>Место получения подарка:</b> {r.place_of_prize}'

            await bot.send_message(chat_id=chat_id, text=m, parse_mode='HTML', reply_markup=get_ikb_info(id, r.is_active))
    await ProfileStatesGroup.show_raffle.set()


async def show_raffles(chat_id):
    await ProfileStatesGroup.raffles.set()
    header = 'Список созданных Вами розыгрышей:\n'
    s = ''
    show_keyboard = InlineKeyboardMarkup(row_width=2)
    with db:
        for r in db.get_raffles():
            if r.finish_date <= datetime.now():
                status = 'Завершен'
            elif r.is_active:
                status = 'Запущен'
            else:
                status = 'Не запущен'
            m = f'\n<b>{r.name}</b>\n' \
                f'<b>Количество участников:</b> {r.users_count}\n' \
                f'<b>Дата окончания:</b> {r.finish_date}\n' \
                f'<b>Статус</b>: {status}\n' \
                f'<b>Место получения подарка:</b> {r.place_of_prize}'
            show_keyboard.add(InlineKeyboardButton(f'{r.name}', callback_data=f'show_raffle_{r.id}'))
            s += m
    await bot.send_message(text=header + s, chat_id=chat_id, parse_mode='HTML', reply_markup=show_keyboard)


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
        await message.answer("Введите информацию о месте получения подарка")
        await ProfileStatesGroup.place.set()


@dp.message_handler(state=ProfileStatesGroup.place)
async def load_desc(message: types.Message, state: FSMContext) -> None:
    if message.text.startswith('/'):
        await message.answer(
            "<b>Название места не может начинаться с /.</b>\nПопробуйте еще раз",
            parse_mode="HTML")
    else:
        async with state.proxy() as data:
            data['place_of_prize'] = message.text
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


def string_to_timestamp(value) -> datetime | None:
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
                media_url=data['photo'],
                place_of_prize=data['place_of_prize']
            )
            with db:
                db.save_raffle(r)
            await message.answer('Вы успешно создали розыгрыш!', reply_markup=get_kb_menu())
            await ProfileStatesGroup.end.set()


if __name__ == '__main__':
    executor.start_polling(dp,
                           skip_updates=True)
