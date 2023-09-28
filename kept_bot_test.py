import aiogram
from aiogram import Bot, Dispatcher, executor, types
from keyboards import kb, ikb
from aiogram.utils.callback_data import CallbackData

TOKEN_API = "6546351543:AAEsBMK9Zl_dBxGHnmoTqw57oQA5iHiy0is"
HELP_COMMAND = """
/start - начать работу
/help - список команд
/give - стикер
"""

bot = Bot(TOKEN_API)
dp = Dispatcher(bot)
cb = CallbackData('ikb', 'action')

async def on_startup(_):
    print('Бот был успешно запущен')



@dp.message_handler(commands=['links'])
async def links_command(message: types.Message):
    await message.answer('Выберите опцию...',
                         reply_markup=ikb)


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer('Добро пожаловать в чат бот <b>Kept raffle bot</b>! \n'
                         'Бот умеет проводить розыгрыши от компании Kept среди студентов ВУЗов Санкт-Петербурга и самостоятельно выбирать победителей! '
                         '\n\n<b>Команды бота:</b> \n/help - помощь \n/give - отправь стикер \n/create - создание розыгрыша ',
                         parse_mode="HTML",
                         reply_markup=kb) #️ get_ikb

@dp.message_handler(commands='vote')
async def vote_command(message: types.Message):
    await bot.send_photo(chat_id=message.from_user.id,
                         photo='https://pazlyigra.ru/uploads/posts/2022-12/479679246.jpg',
                         caption='Нравится тебе фото?',
                         reply_markup=ikb)


@dp.callback_query_handler()
async def callback_vote(callback: types.CallbackQuery):
    if callback.data == 'Like':
        await callback.answer("Ты любишь котов")
    await callback.answer("Тебе не нравятся коты")


@dp.message_handler(commands=['give'])
async def start_command(message: types.Message):
    await bot.send_sticker(message.from_user.id,
                           sticker="CAACAgIAAxkBAAEKWiVlDF4ygh7JNn_tE8aU3aV98-TcXgACqiAAAg5wMEn7uAfFEMjZ-zAE")
    await message.delete()


@dp.message_handler(commands=['help'])
async def helf_command(message: types.Message):
    await message.reply(text=HELP_COMMAND)
    await message.delete()


@dp.message_handler()
async def send_emoji(message: types.Message):
    await message.answer(text='Я вас не понял' + '😢')
    await message.delete()

@dp.callback_query_handler(cb.filter(action = 'push 1'))
async def push_fisrt_to_handler(callback: types.CallbackQuery):
        await callback.answer('Hello!')

@dp.callback_query_handler(cb.filter(action = 'push 2'))
async def push_to_to_handler(callback: types.CallbackQuery):
        await callback.answer('World!')

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
