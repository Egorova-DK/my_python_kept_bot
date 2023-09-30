from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram import dispatcher

cb = CallbackData('ikb', 'media')
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






