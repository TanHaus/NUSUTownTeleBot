import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import pandas as pd


def start(update, context):
    update.message.reply_text("UwU")
    '''
    someone can write some instructions here
    '''

def help(update, context):
    update.message.reply_text("Hewp! :o")

def show_stores(update, context):
    keyboard = []
    for i in categories:
        keyboard.append([InlineKeyboardButton(i, callback_data=i)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose a category', reply_markup = reply_markup)

    return 'handle_category'

def handle_category(update, context):
    query = update.callback_query
    '''
    keyboard = []
    for i in categories:
        keyboard.append([InlineKeyboardButton(i)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text('Please choose a category', reply_markup = reply_markup)
    '''
    query.message.reply_text("Selected option: {}".format(query.data))

    keyboard = []
    for i in opening_hours[opening_hours['Category']==query.data]['Store']:
        print(i)
        keyboard.append([InlineKeyboardButton(i, callback_data=i)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.reply_text('Please choose a store', reply_markup = reply_markup)

    return 'handle_store'

def handle_store(update, context):
    query = update.callback_query
    today = pd.Timestamp.today()

    store_opening_hours = opening_hours[opening_hours.Store==query.data]['Term Opening Hours (' + today.day_name()[0:3] + ')'].to_numpy()[0]
    start_time = store_opening_hours[:store_opening_hours.find('-')]
    end_time = store_opening_hours[store_opening_hours.find('-')+1:]
    is_open = 'not'
    if int(start_time)<today.hour<int(end_time): is_open = ''
    
    query.message.reply_text("{} is {} open".format(query.data, is_open))
    query.message.reply_text('Opening hours: {}'.format(store_opening_hours))
    

    return

def main():
    #token = input('Please enter the UTown bot token: ')
    token = '640769917:AAFoD9m-vyOaQ6sTbyW7ah-RGJW1XPD6c6A'
    
    updater = Updater(token, use_context=True)

    dp = updater.dispatcher

    buttons = []

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    # dp.add_handler(CommandHandler("stores", show_stores))
    # dp.add_handler(CallbackQueryHandler(button))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('stores', show_stores)],
        states={
            'handle_category': [CallbackQueryHandler(handle_category)],
            'handle_store': [CallbackQueryHandler(handle_store)]
        },
        fallbacks=[CommandHandler("stores", show_stores)]
    )

    dp.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()

if __name__=='__main__':
        # Create Pandas Dataframe
    opening_hours = pd.read_excel('Utown Outlets Opening Hours.xlsx',
                                  header=0,
                                  index_col=False,
                                  keep_default_na=True
                                  )
    categories = opening_hours['Category'].unique()
    stores = opening_hours['Store']
    main()
