import asyncio
import random
from datetime import datetime
from itertools import product

from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ChatMemberStatus
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sys import argv

from config import TOKEN_API
from keyboards import get_kb_menu, cb2, get_ikb_info, get_ikb_edit, get_ikb_menu, cb, get_ikb_media
from database import Database, Raffle, Channel, User
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

storage = MemoryStorage()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot,
                storage=storage)
db = Database()

sched = AsyncIOScheduler()
sched.start()

kb = InlineKeyboardMarkup()
kb.add(InlineKeyboardButton('Удалить', callback_data='delete_1'))

ID_CHANNEL = argv[1]

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
    edit_users_count = State()
    edit_place = State()
    engage = State()
    place = State()


async def on_startup(_):
    print('Бот был успешно запущен')


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
        await message.answer('Добро пожаловать в чат бот <b>Kept raffle bot</b>! 👋 \n'
                             'Бот умеет проводить розыгрыши от компании Kept среди студентов ВУЗов Санкт-Петербурга и '
                             'самостоятельно выбирать победителей! '
                             '\n\n<b>Команды бота:</b> \n/create_raffle - создание розыгрыша \n/raffles - просмотр '
                             'розыгрышей и работа с ними',
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
                        await message.answer('Вы уже участвуете в розыгрыше!🥳🎁')
                        return
                await ProfileStatesGroup.engage.set()
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton('Участвовать 🍀', callback_data=f'Engage_{r.id}')],
                ])
                text = f'{r.name}\n{r.description}\n Дата подведения итогов:{r.finish_date}'
                if r.media_url:
                    a = r.media_url
                    type = a[:5]
                    media_url = a[5:]
                    if type == 'photo':
                        await bot.send_photo(chat_id=message.from_user.id,
                                             photo=media_url,
                                             caption=text,
                                             reply_markup=kb,
                                             parse_mode='HTML')
                    elif type == 'video':
                        await bot.send_video(chat_id=message.from_user.id,
                                             video=media_url,
                                             caption=text,
                                             reply_markup=kb,
                                             parse_mode='HTML')
                else:
                    await bot.send_message(chat_id=message.from_user.id,
                                           text=text,
                                           parse_mode='HTML',
                                           reply_markup=kb)
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
            await callback.message.edit_reply_markup(reply_markup=None)
            await bot.send_message(chat_id=callback.from_user.id,
                                   text=f'<b>Вы успешно зарегистрировались на розыгрыш!👏</b>\n'
                                        f'Ваш уникальный код: <b>{u.ticket_number}</b>',
                                   parse_mode='HTML')

    else:
        link = await bot.create_chat_invite_link(ID_CHANNEL)
        await callback.answer(cache_time=1)
        await bot.send_message(
            chat_id=callback.from_user.id,
            text=f'Сначала вступите в телеграмм канал "Созвездие - СПб" ⬇️\n{link.invite_link}',
            parse_mode='HTML',
        )



@dp.callback_query_handler(cb2.filter(menu='Menu'), state='*')
async def menu_to_handler(callback: types.CallbackQuery):
    await bot.send_message(callback.from_user.id,
                           'Бот умеет проводить розыгрыши от компании Kept среди студентов ВУЗов Санкт-Петербурга и '
                           'самостоятельно выбирать победителей!'
                           '\n\n<b>Команды бота:</b> \n/create_raffle - создание розыгрыша \n/raffles - просмотр '
                           'розыгрышей и работа с ними',
                           parse_mode="HTML",
                           reply_markup=get_kb_menu())
    await ProfileStatesGroup.menu.set()
    await callback.message.edit_reply_markup()


@dp.message_handler(commands=['raffles'], state='*')
@dp.message_handler(text=['Розыгрыши'], state='*')
async def cmd_show_raffles(message: types.Message) -> None:
    member = await bot.get_chat_member(ID_CHANNEL, message.from_user.id)
    if member.is_chat_admin():
        await message.delete()
        await show_raffles(message.from_user.id)
        await ProfileStatesGroup.raffles.set()


@dp.callback_query_handler(state=ProfileStatesGroup.show_raffle, text_startswith='edit_')
async def edit_raffle(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    id = callback.data.split('_')[-1]
    await bot.send_message(chat_id=callback.from_user.id, text='Что бы Вы хотели изменить? 🤔', parse_mode='HTML',
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


@dp.callback_query_handler(state=[ProfileStatesGroup.raffles, ProfileStatesGroup.show_raffle], text_startswith='show_raffle_')
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
            global sched
            sched.remove_all_jobs()
            sched.add_job(finish_raffle, kwargs={'raffle_id': r.id}, trigger='date', next_run_time=r.finish_date)
            await bot.send_message(chat_id=callback.from_user.id, text='<b>Ваш розыгрыш успешно запущен! 👏</b>',
                                   parse_mode='HTML')
        await show_raffle_id(id, chat_id=callback.from_user.id)


@dp.callback_query_handler(state=ProfileStatesGroup.show_raffle, text_startswith='complete_')
async def complete_raffle(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    id = callback.data.split('_')[-1]
    with db:
        r = db.get_raffles(int(id))
        if r.is_active:
            await finish_raffle(int(id))
        await bot.send_message(chat_id=callback.from_user.id, text='Розыгрыш завершен!')


async def finish_raffle(raffle_id: int):
    with db:
        r = db.get_raffles(raffle_id)
        r.is_active = False
        r.finish_date = datetime.now()
        db.update_raffle(r)
        users = db.get_user_by_raffle_id(raffle_id)
        if len(users) != 0:
            winner = users[random.randint(0, len(users) - 1)]
            for user in users:
                if user == winner:
                    await bot.send_message(chat_id=user.telegram_id,
                                           text=f'<i>Поздравляем!🥳 \nВы победили в розыгрыше <b>{r.name}</b>!</i>',
                                           parse_mode='HTML')
                    await bot.send_message(chat_id=user.telegram_id,
                                           text=f'📍Забрать приз Вы сможете по адресу <b>{r.place_of_prize}</b>',
                                           parse_mode='HTML')
                else:
                    await bot.send_message(chat_id=user.telegram_id,
                                           text=f'Вы проиграли в розыгрыше <b>{r.name}!</b>😔',
                                           parse_mode='HTML')
    admins = await bot.get_chat_administrators(ID_CHANNEL)
    for admin in admins:
        if admin.user.is_bot:
            continue
        if len(users) == 0:
            await bot.send_message(chat_id=admin.user.id,
                                   text='Время проведения вышло. В розыгрыше не участвовал ни один человек',
                                   parse_mode='HTML')
        else:
            button_url = f'tg://user?id={winner.telegram_id}'
            print(button_url)
            await bot.send_message(chat_id=admin.user.id,
                                   text=f'В розыгрыше <b>{r.name}</b> определен победитель под номером {winner.ticket_number}.'
                                        f'Нажмите на кнопку, чтобы связаться с ним ⬇️',
                                   parse_mode='HTML',
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Победитель 🎁", url=button_url)]
                ]))


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
            "<b>Информация о месте и времени получения подарка не может начинаться с /.</b>\nПопробуйте еще раз",
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
    await bot.send_message(chat_id=callback.from_user.id, text='<b>Введите новое название розыгрыша</b>',
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


@dp.callback_query_handler(state=ProfileStatesGroup.show_raffle, text_startswith='Users_count_')
async def show_edit_name_raffle(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    id = callback.data.split('_')[-1]
    async with state.proxy() as data:
        data['edit_user_count'] = id
    await bot.send_message(chat_id=callback.from_user.id, text='<b>Введите количество участников</b>',
                           parse_mode='HTML')
    await ProfileStatesGroup.edit_users_count.set()


@dp.message_handler(state=ProfileStatesGroup.edit_users_count)
async def edit_name_raffle(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(
            "Введите корректное количество участников",
            parse_mode="HTML")
    else:
        async with state.proxy() as data:
            id = data['edit_user_count']
            data['edit_user_count'] = None
        with db:
            r = db.get_raffles(id)
            r.users_count = int(message.text)
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
                           text='<b>Введите новую дату окончания розыгрыша</b> в формате (ЧЧ:ММ ДД.ММ.ГГГГ). '
                                '<b>Например</b>: 12:00 31.12.2023.',
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
            global sched
            sched.remove_all_jobs()
            sched.add_job(finish_raffle, kwargs={'raffle_id': r.id}, trigger='date', next_run_time=r.finish_date)
        await show_raffle_id(id, chat_id=message.from_user.id)


async def show_raffle_id(id, chat_id):
    with db:
        r = db.get_raffles(id)
        if r.finish_date <= datetime.now():
            status = 'Завершен ⌛️'
        elif r.is_active:
            status = 'Запущен ⏳'
        else:
            status = 'Не запущен 🕖'
        m = f'<i>{r.name}</i>\n' \
            f'\n{r.description}\n' \
            f'<b>Количество участников:</b> {r.users_count}\n' \
            f'<b>Дата окончания:</b> {r.finish_date}\n' \
            f'<b>Статус:</b> {status}\n' \
            f'<b>📍Место и время получения подарка:</b> {r.place_of_prize}'
        if r.media_url:
            a = r.media_url
            print(r.media_url)
            type = a[:5]
            print(type)
            media_url = a[5:]
            print(media_url)
            if type == 'photo':
                await bot.send_photo(chat_id=chat_id,
                                     photo=media_url,
                                     caption=m,
                                     parse_mode='HTML',
                                     reply_markup=get_ikb_info(id, r.is_active))
            elif type == 'video':
                await bot.send_video(chat_id=chat_id,
                                     video=media_url,
                                     caption=m,
                                     parse_mode='HTML',
                                     reply_markup=get_ikb_info(id, r.is_active))
        else:
            await bot.send_message(chat_id=chat_id, text=m, parse_mode='HTML',
                                   reply_markup=get_ikb_info(id, r.is_active))
    await ProfileStatesGroup.show_raffle.set()


async def show_raffles(chat_id):
    await ProfileStatesGroup.raffles.set()
    with db:
        r = db.get_raffles()
        if len(r) == 0:
            await bot.send_message(text='Вы пока не создали ни один розыгрыш',chat_id=chat_id, parse_mode='HTML')
        else:
            header = 'Список созданных Вами розыгрышей:\n'
            s = ''
            show_keyboard = InlineKeyboardMarkup(row_width=2)
            with db:
                for r in db.get_raffles():
                    if r.finish_date <= datetime.now():
                        status = 'Завершен ⌛️'
                    elif r.is_active:
                        status = 'Запущен ⏳'
                    else:
                        status = 'Не запущен 🕖'
                    m = f'\n<i>{r.name}</i>:\n' \
                        f'\n<b>Количество участников:</b> {r.users_count}\n' \
                        f'<b>Дата окончания:</b> {r.finish_date}\n' \
                        f'<b>Статус</b>: {status}\n' \
                        f'<b>📍Место и время получения подарка:</b> {r.place_of_prize}\n'
                    show_keyboard.add(InlineKeyboardButton(f'{r.name}', callback_data=f'show_raffle_{r.id}'))
                    s += m
            await bot.send_message(text=header + s, chat_id=chat_id, parse_mode='HTML', reply_markup=show_keyboard)


# Создание розыгрыша
@dp.message_handler(commands=['create_raffle'], state='*')
@dp.message_handler(text=['Создать розыгрыш'], state='*')
async def cmd_create_raffle(message: types.Message) -> None:
    member = await bot.get_chat_member(ID_CHANNEL, message.from_user.id)
    if member.is_chat_admin():
        await message.answer(text='Сейчас мы создадим розыгрыш 😌', reply_markup=types.ReplyKeyboardRemove())
        await message.answer(
            "<b>Введите название розыгрыша</b>\n"
            "Это название будет отображаться у участника в списке розыгрышей в боте.",
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
            '<b>Введите текст подробного описания розыгрыша.</b>\n'
            'Введенный текст будет отображаться у участника в списке розыгрышей в боте.',
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
        await message.answer("Введите информацию о месте и времени получения подарка. Введенный текст будет отправлен "
                             "победителю розыгрыша после подведения итогов", reply_markup=get_ikb_menu())
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
        await message.answer("Хотите добавить картинку или видео для розыгрыша?",
                             reply_markup=get_ikb_media())
        await ProfileStatesGroup.media_question.set()


@dp.callback_query_handler(cb.filter(media='No'), state=ProfileStatesGroup.media_question)
async def no_media_to_handler(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['media'] = None
    await bot.send_message(callback.from_user.id,
                           '<b>Укажите время завершения розыгрыша</b> в формате (ЧЧ:ММ ДД.ММ.ГГГГ).\n'
                           '<b>Например:</b> 12:00 31.12.2023',
                           parse_mode="HTML", reply_markup=get_ikb_menu())
    await ProfileStatesGroup.finish_date.set()
    await callback.message.delete()


@dp.callback_query_handler(cb.filter(media='Yes'), state=ProfileStatesGroup.media_question)
async def yes_media_to_handler(callback: types.CallbackQuery):
    await bot.send_message(callback.from_user.id,
                           '<b>Вставьте картинку или видео</b>',
                           parse_mode="HTML")
    await ProfileStatesGroup.media.set()
    await callback.message.edit_reply_markup()


@dp.message_handler(lambda message: not message.photo or not message.video, state=ProfileStatesGroup.media)
async def check_photo(message: types.Message):
    await message.reply('Отправьте видео или фотографию!')

@dp.message_handler(content_types=['photo'], state=ProfileStatesGroup.media)
async def load_media(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['media'] = 'photo'+message.photo[0].file_id
    await message.answer(
        '<b>Укажите время завершения розыгрыша</b> в формате (ЧЧ:ММ ДД.ММ.ГГГГ).\n'
        '<b>Например:</b> 12:00 31.12.2023',
        parse_mode="HTML", reply_markup=get_ikb_menu())
    await ProfileStatesGroup.finish_date.set()


@dp.message_handler(content_types=['video'], state=ProfileStatesGroup.media)
async def load_media(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['media'] = 'video'+message.video.file_id
    await message.answer(
        '<b>Укажите время завершения розыгрыша</b> в формате (ЧЧ:ММ ДД.ММ.ГГГГ).\n'
        '<b>Например:</b> 12:00 31.12.2023',
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
            await message.answer('Некорректная дата. Попробуйте еще раз', reply_markup=get_ikb_menu())
        else:
            r = Raffle(
                name=data['name'],
                finish_date=finish_date,
                description=data['description'],
                media_url=data['media'],
                place_of_prize=data['place_of_prize']
            )
            with db:
                db.save_raffle(r)
                id = r.id
            await message.answer('Вы успешно создали розыгрыш! 👏', reply_markup=get_kb_menu())
            await show_raffle_id(id, message.from_user.id)
            await ProfileStatesGroup.show_raffle.set()


if __name__ == '__main__':
    with db:
        r = db.get_first_raffle()
        if r is not None:
            if r.finish_date > datetime.now():
                sched.remove_all_jobs()
                sched.add_job(finish_raffle, kwargs={'raffle_id': r.id}, trigger='date', next_run_time=r.finish_date)
            else:
                asyncio.run(finish_raffle(r.id))
    executor.start_polling(dp,
                           skip_updates=True)
