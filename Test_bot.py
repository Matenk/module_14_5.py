from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from admin import *
from db import *
from crud_functions import *
from key import API
from aiogram.dispatcher import FSMContext
import asyncio
from keyboards import *
from texts import *
import re
bot = Bot(token=API)
dp = Dispatcher(bot, storage=MemoryStorage())




"""
КЛАСС СОСТОЯНИЙ ДЛЯ РАСЧЕТА СУТОЧНОЙ КАЛЛОРИЙНОСТИ:
"""
class UserState(StatesGroup):

    age = State()
    growth = State()
    weight = State()


@dp.callback_query_handler(text='calories')
async def set_age(call):
    await call.message.answer(age_) # среагировал на кнопку и запросил возраст
    await call.answer()
    await UserState.age.set() # установил состояние возраст


@dp.message_handler(state=UserState.age) # хендлер перехватил состояние возраст
async def set_growth(message, state): # ф-я принимает и состояние и текст который уйдет в состояние возраст
    if not message.text.isdigit() or not (
            0 < int(message.text) < 120):
        await message.answer('Пожалуйста, введите корректный возраст (число от 1 до 120).')
        return
    await state.update_data(age=message.text) # в состояние возраста улетает сообщение пользователя (ключ = значение)
    if int(message.text) % 10 == 1 and int(message.text) % 100 != 11:
        word = 'год'
    elif int(message.text) % 100 in [2, 3, 4] and int(message.text) % 100 not in [12, 13, 14]:
        word = 'года'
    else:
        word = 'лет'
    await message.answer(f'Целых {message.text} {word}...'
                         f'и как ты справляешься с такими высокими технологиями в твоем-то возрасте? {growth_}') #
    # запросили рост
    await UserState.growth.set() # установили новое состояние (теперь для роста)

@dp.message_handler(state=UserState.growth) # хэндлер перехватил состояние возраст
async def set_weight(message, state):
    if not message.text.isdigit() or not (50 < int(message.text) < 300):
        await message.answer('Пожалуйста, введите корректный рост (число от 50 до 300 сантиметров).')
        return
    await state.update_data(growth=message.text) # в состояние роста улетает сообщение (ключ = значение)
    await message.answer(weight_) # запрос веса
    await UserState.weight.set() # установили состояние для веса

@dp.message_handler(state=UserState.weight) # перехватили состояние веса
async def send_calories(message, state): # ф-я приняла сообщение от пользов-ля и наше перехваченное состояние, а затем
    if not message.text.isdigit() or not (20 < int(message.text) < 300):
        await message.answer('Пожалуйста, введите корректный вес (число от 20 до 300 кг).')
        return
    await state.update_data(weight=message.text) # в состояние веса улетает сообщение
    # (получается словарь из параметра weight и сообщения пользователя)
    # т.е мы занесли сообщение пользователя о весе в условную базу данных этого состояние в виде словаря
    data = await state.get_data() # переменная через которую мы получаем все данные состояний из словарей
    w = data["weight"] # т.к. данные были записаны в виде словарей соответственно вытаскиваем их по ключу (["weight"] итд)
    g = data["growth"]
    a = data["age"]
    calories = 10 * int(w) + int(6.25) * int(g) - 5 * int(a) + 5
    await message.answer(f'Ууу, дорогуша, твоя суточная норма ккал: {calories}, крч столько сколько ты съела сегодня на завтрак...\n Пока!')
    await state.finish() # закрытие машины состояний для сохранения состояния



"""
КЛАСС СОСТОЯНИЙ ДЛЯ РЕГИГСТРАЦИИ ПОЛЬЗОВАТЕЛЕЙ:
"""
class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()
    balance = 1000

@dp.message_handler(text='Регистрация')
async def sing_up(message):
    await message.answer('Введите имя пользователя (только латинский алфавит):')
    await RegistrationState.username.set()

@dp.message_handler(state=RegistrationState.username)
async def set_username(message, state):
    while True:
        check_name = is_included(message.text)
        if check_name is True:
            await message.answer('Пользователь существует, введите другое имя!')
            return
        else:
            await state.update_data(username=message.text)
            break
    await message.answer('Введите свой email:')
    await RegistrationState.email.set()

pattern_email = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+$" # регулярное выражение (т.е. шаблон)
# для проверки формата email

@dp.message_handler(state=RegistrationState.email)
async def set_email(message, state):
    match = re.match(pattern_email, message.text) # метод re.match проверяет соответсвует ли строка,
    # которую ввел пользователь нашему выражению (шаблону) который мы заранее прописали
    if match is None: # если вводимый email не соответствует нашему шаблону, то возвращается None
        await message.answer('Неправильный формат почты, попробуйте снова')
    else: # в любом другом случае (т.е когда not None, а значит email соответствует шаблону)
        # email принимается и записывается в словарь нашего состояния (в параметр email=)
        await state.update_data(email=message.text)
        await message.answer('Введите свой возраст:')
        await RegistrationState.age.set()

@dp.message_handler(state=RegistrationState.age)
async def set_age(message, state):
    if not message.text.isdigit() or not (1 <= int(message.text) <= 120):
        await message.answer('Пожалуйста, введите корректный возраст (число от 1 до 120).')
    else:
        await state.update_data(age=message.text)
        data = await state.get_data()
        add_user(data['username'], data['email'], data['age'])
        await message.answer('Регистрация прошла успешно!')
        await state.finish()



"""
СПИСОК ТОВАРОВ ИЗ БАЗЫ ДАННЫХ:
"""
products = get_all_products()
@dp.message_handler(text='Купить')
async def get_buying_list(message):
    for product in products:
        id, title, description, price = product
        image_path = f'img/{title.lower()}.jpg'
        with open(image_path, 'rb') as file:
            await message.answer_photo(file, caption=f' {title} | {description} | {price}\n')

    await message.answer('Выберите продукцию', reply_markup=kb_catalog)


"""
ПОКУПКА ТОВАРА:
"""
@dp.callback_query_handler(text='product_buying')
async def send_confirm_message(call):
    await call.message.answer(buy_complete)
    await call.answer()


"""
ПОМОЩЬ АДМИНА:
"""
@dp.callback_query_handler(text='other')
async def other_mes(call):
    await call.message.answer(other)
    await call.answer()


"""
ФОРМУЛА ПОДСЧЕТА ККАЛ:
"""
@dp.callback_query_handler(text='formulas')
async def get_formulas(call):
    await call.message.answer(formula)
    await call.answer()


"""
МЕНЮ (ФОРМУЛА, РАСЧЕТ ККАЛ: )
"""
@dp.message_handler(text='Расчет')
async def main_menu(message):
    await message.answer('Выбери опцию', reply_markup=kb2)

"""
ИНФО О БОТЕ:
"""
@dp.message_handler(text='Информация')
async def info(message):
    await message.answer(all_info)


"""
СТАРТОВОЕ МЕНЮ:
"""
@dp.message_handler(commands=['start'])
async def start_message(message):
    with open('img/hello.jpg', 'rb') as file:
        await message.answer_photo(file, caption=f'Привет, {message.from_user.username.capitalize()}! ' + start, reply_markup=start_kb)


"""
ХЭНДЛЕР ДЛЯ ПЕРЕХВАТА ЛЮБЫХ СООБЩЕНИЙ:
"""
@dp.message_handler()
async def all(message):
    await message.answer(all_mess)




if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
