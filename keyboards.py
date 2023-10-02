from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

cb = CallbackData('ikb', 'media')
cb2 = CallbackData('ikb', 'menu')
cb4 = CallbackData('ikb', 'edit')

def get_kb_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Создать розыгрыш")).add(KeyboardButton("Розыгрыши"))
    return kb


def get_ikb_media() ->InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton('Нет', callback_data=cb.new('No'))],
    [InlineKeyboardButton('Да', callback_data=cb.new('Yes'))],
    ])
    return ikb

def get_ikb_menu() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Выйти в меню', callback_data=cb2.new('Menu'))]
        ])
    return ikb

def get_ikb_info(id) -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Запустить розыгрыш', callback_data=f'run_{id}')],
        [InlineKeyboardButton('Редактировать розыгрыш', callback_data=f'edit_{id}')],
        [InlineKeyboardButton('Удалить розыгрыш', callback_data=f'delete_{id}')],
        [InlineKeyboardButton('Назад', callback_data='raffles')],
        ])
    return ikb

def get_ikb_edit(id) -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Название', callback_data=cb4.new(f'Name_{id}'))],
        [InlineKeyboardButton('Описание', callback_data=cb4.new(f'Discription_{id}'))],
        [InlineKeyboardButton('Количество участников', callback_data=cb4.new(f'Count_user_{id}'))],
        [InlineKeyboardButton('Назад', callback_data=cb4.new(f'show_raffle_{id}'))],
        ])
    return ikb





