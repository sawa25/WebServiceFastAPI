from telegram.ext import Application, CommandHandler, MessageHandler, filters,CallbackQueryHandler
from telegram import InlineKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from dotenv import load_dotenv
import os
import sys

# подгружаем переменные окружения
load_dotenv()
userinterface={}
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

# токен бота
TOKEN = os.getenv('TG_TOKEN')
# INLINE
# форма inline клавиатуры
inline_frame = [[InlineKeyboardButton("English", callback_data="en")],
                [InlineKeyboardButton("Русский", callback_data="ru")],
                ]
# создаем inline клавиатуру
inline_keyboard = InlineKeyboardMarkup(inline_frame)


# функция-обработчик команды /start
async def start(update: Update, _):
    # прикрепляем inline клавиатуру к сообщению
    await update.message.reply_text("Привет! Выберите язык интерфейса.\nHello!Choose the interface language.", 
                                    reply_markup=inline_keyboard)

def interface(id:str)->str:
    global userinterface
    if userinterface[id]=="ru":
        return "ru"
    elif userinterface[id]=="en":
        return "en"
    else:
        return "ru"
# функция-обработчик текстовых сообщений
async def text(update, context):
    if interface(update.message.from_user.id)=="ru":
        mes="Мы получили от тебя текстовое сообщение!"
    elif interface(update.message.from_user.id)=="en":
        mes="We’ve received a message from you!"
    await update.message.reply_text(mes)
# функция-обработчик голосовых сообщений
async def voice(update, context):
    if interface(update.message.from_user.id)=="ru":
        mes="Голосовое сообщение получено"
    elif interface(update.message.from_user.id)=="en":
        mes="We’ve received a voice message from you!"
    await update.message.reply_text(mes)
# функция-обработчик сообщений с изображениями
async def image(update, context):
    global script_dir
    # получаем изображение из апдейта
    file = await update.message.photo[-1].get_file()
    # сохраняем изображение на диск
    await file.download_to_drive(f"{script_dir}/photos/image.jpg")
    if interface(update.message.from_user.id)=="ru":
        mes="Фотография сохранена"
    elif interface(update.message.from_user.id)=="en":
        mes="Photo saved!"
    await update.message.reply_text(mes)

# функция-обработчик нажатий на кнопки
async def button(update: Update, _):
    global userinterface
    # получаем callback query из update
    query = update.callback_query
    # всплывающее уведомление
    await query.answer(f'{query.data}\n{script_dir}')
    # сохранить для данного пользователя язык интерфейса
    userinterface[query.from_user.id]=query.data

def main():
    # создаем приложение и передаем в него токен
    application = Application.builder().token(TOKEN).build()
    print('Бот запущен...')

    # добавляем обработчик команды /start
    application.add_handler(CommandHandler("start", start))
    # добавляем CallbackQueryHandler (только для inline кнопок)
    application.add_handler(CallbackQueryHandler(button))

    # добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT, text))
    # добавляем обработчик голосовых сообщений
    application.add_handler(MessageHandler(filters.VOICE, voice))
    # добавляем обработчик сообщений с фотографиями
    application.add_handler(MessageHandler(filters.PHOTO, image))

    # запускаем бота (нажать Ctrl-C для остановки бота)
    application.run_polling()
    print('Бот остановлен')


if __name__ == "__main__":
    main()