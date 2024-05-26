from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from dotenv import load_dotenv
import openai
import os
import requests
import aiohttp
import json
from collections import deque



# подгружаем переменные окружения
load_dotenv()

# передаем секретные данные в переменные
TOKEN = os.environ.get("TG_TOKEN")
GPT_SECRET_KEY = os.environ.get("GPT_SECRET_KEY")

# передаем секретный токен chatgpt
openai.api_key = GPT_SECRET_KEY


# функция для синхронного общения с chatgpt
async def get_answer(text):
    payload = {"text":text}
    response = requests.post("http://127.0.0.1:5000/api/get_answer", json=payload)
    return response.json()


# функция для асинхронного общения с сhatgpt
async def get_answer_async(text):
    payload = {"text":text}
    async with aiohttp.ClientSession() as session:
        async with session.post('http://127.0.0.1:5000/api/get_answer_async', json=payload) as resp:
            return await resp.json()


# функция-обработчик команды /start 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # при первом запуске бота добавляем этого пользователя в словарь
    if update.message.from_user.id not in context.bot_data.keys():
        # Создаем очередь с максимальным размером 5
        queue = deque(maxlen=5)
        # хранить в словаре кортеж -
        # количество оставшихся запросов и очередь последних 5 вопросов и ответов
        context.bot_data[update.message.from_user.id] = (3,queue)

    
    # возвращаем текстовое сообщение пользователю
    await update.message.reply_text('Задайте любой вопрос ChatGPT')


# функция-обработчик команды /data 
async def data(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # создаем json и сохраняем в него словарь context.bot_data
    with open('data.json', 'w') as fp:
        json.dump(context.bot_data, fp)
    
    # возвращаем текстовое сообщение пользователю
    await update.message.reply_text('Данные сгружены')


# функция-обработчик текстовых сообщений
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # проверка доступных запросов пользователя
    # очередь хранится во втором элементе кортежа
    (reqcnt,queue)=context.bot_data[update.message.from_user.id]
    if reqcnt > 0:

        # выполнение запроса в chatgpt
        first_message = await update.message.reply_text('Ваш запрос обрабатывается, пожалуйста подождите...')
        # предшествующий диалог+последний вопрос
        dial=""
        for i,dicqa in enumerate(queue):
            dial=f'{dial}\nВопрос{i}:{dicqa["question"]}\nОтвет{i}:{dicqa["answer"]}'
        # последний вопрос пользователя
        dial=f"{dial}\nПоследний вопрос:{update.message.text}"
        await context.bot.edit_message_text(text=f"Передан предшествующий диалог и очередной вопрос:\n{dial}", chat_id=update.message.chat_id, message_id=first_message.message_id)
        res = await get_answer_async(dial)
        await update.message.reply_text(f'Ответ: {res["message"]}')
        # составить очередную пару вопрос-ответ
        nextq= {"question": update.message.text,"answer": res['message']}
        queue.append(nextq)
        # уменьшаем количество доступных запросов на 1
        # количество хранится в первом элементе кортежа
        reqcnt-=1
        context.bot_data[update.message.from_user.id]=(reqcnt,queue)
        await update.message.reply_text(f'Осталось запросов: {reqcnt}')
    
    else:

        # сообщение если запросы исчерпаны
        await update.message.reply_text('Ваши запросы на сегодня исчерпаны')


# функция, которая будет запускаться раз в сутки для обновления доступных запросов
async def callback_daily(context: ContextTypes.DEFAULT_TYPE):

    # проверка базы пользователей
    if len(context.bot_data)>0:
        # проходим по всем пользователям в базе и обновляем их доступные запросы
        for key in context.bot_data:
            (_,queue)=context.bot_data[key]
            context.bot_data[key] = (6,queue)
        print('Запросы пользователей обновлены')
    else:
        print('Не найдено ни одного пользователя')


def main():

    # создаем приложение и передаем в него токен бота
    application = Application.builder().token(TOKEN).build()
    print('Бот запущен...')

    # создаем job_queue 
    job_queue = application.job_queue
    job_queue.run_repeating(callback_daily, # функция обновления базы запросов пользователей
                            interval=60,    # интервал запуска функции (в секундах)
                            first=10)       # первый запуск функции (через сколько секунд)

    # добавление обработчиков
    application.add_handler(CommandHandler("start", start, block=True))
    application.add_handler(CommandHandler("data", data, block=True))
    application.add_handler(MessageHandler(filters.TEXT, text, block=True))

    # запуск бота (нажать Ctrl+C для остановки)
    application.run_polling()
    print('Бот остановлен')


if __name__ == "__main__":
    main()