from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram import dispatcher

kb = ReplyKeyboardMarkup(resize_keyboard=True,
                         one_time_keyboard=True)

b1 = KeyboardButton(text='/help')
b2 = KeyboardButton(text='/vote')
kb.add(b1,b2)


ikb = InlineKeyboardMarkup(row_width=2)
ib1 = InlineKeyboardButton(text='Да',
                           callback_data="Like")

ib2 = InlineKeyboardButton(text= 'Нет',
                           callback_data="Dislike")

ikb.add(ib1, ib2)


cb = CallbackData('ikb', 'action')

def get_ikb():
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Button 1', callback_data=cb.new('push 1'))], #️callback_data = {'action': push 1}
        [InlineKeyboardButton('Button 2', callback_data=cb.new('push 2'))],
    ])
    return ikb




