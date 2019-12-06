from TextToOwO import owo
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

def start(update, context):
    update.message.reply_text("UwU")

def help(update, context):
    update.message.reply_text("Hewp! :o")

def handle_text(update, context):
    update.message.reply_text(owo.text_to_owo(update.message.text))


def main():
    token = input('Please enter the UTown bot token: ')

    updater = Updater(token, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    #dp.add_handler(CommandHandler("get_joke", getjoke))

    dp.add_handler(MessageHandler(Filters.text, handle_text))

    updater.start_polling()

    updater.idle()

if __name__=='__main__':
    main()