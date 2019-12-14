import os
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import pandas as pd


# Command functions

def start(update, context):
    update.message.reply_text("Welcome to the NUS Utown TeleBot!\n" +
    "Ever been hungry in the middle of the night and dying to know which food stores are still open? " +
    "Or wondered to know what are the retail and sporting options here in Utown?\n" 
    "Then you have come to the right place. Created by TanHaus, this Bot aims to provide useful information about the shops and amenities available in the Utown Campus. " +
    "To help you enhance your Utown experience, you may find the following commands useful:\n" +
    "/stores: Shows the directory of Utown shops and amenities. \n /open: Shows all stores that are currently open.")

def show_stores(update, context):
    keyboard = []
    for i in categories:
        keyboard.append([InlineKeyboardButton(i, callback_data=i)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose a category', reply_markup = reply_markup)

    return 'handle_category'

def show_open_stores(update, context):
    #today = pd.Timestamp.today()
    open_stores = ''
    column_label_today = 'Term Opening Hours (' + today.day_name()[0:3] + ')'
    for index in opening_hours.index:
        store_opening_hours = opening_hours.loc[index, column_label_today]
        if is_open_today(store_opening_hours): 
            open_stores += (opening_hours.loc[index, 'Store'] + '\t(' + store_opening_hours + ')' + '\n')

    update.message.reply_text('The following stores are still open:\n{}'.format(open_stores))

    opening_hours['Open?'] = opening_hours['Store'].apply(is_open_today)
    update.message.reply_text(opening_hours[opening_hours['Open']][Store])


    
        
# Handle functions

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
        keyboard.append([InlineKeyboardButton(i, callback_data=i)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.reply_text('Please choose a store', reply_markup = reply_markup)

    return 'handle_store'

def handle_store(update, context):
    query = update.callback_query
    #today = pd.Timestamp.today()
    store_opening_hours = opening_hours[opening_hours.Store==query.data]['Term Opening Hours (' + today.day_name()[0:3] + ')'].to_numpy()[0]
    
    if store_opening_hours == 'Closed':
        query.message.reply_text("{} is closed".format(query.data))
        #tell user when the store opens

    elif is_open_today(store_opening_hours):
        query.message.reply_text("{} is open".format(query.data))
        query.message.reply_text('Opening hours: {}'.format(store_opening_hours))

    else:
        query.message.reply_text("{} is closed".format(query.data))
        #tell user when the store opens

        '''
        if len(store_opening_hours) == 9:
            start_time, end_time = store_opening_hours.split('-')    
            if int(start_time)<int(today.strftime('%H%M'))<int(end_time): is_open = True
        else:
            store_opening_hours_1, store_opening_hours_2 = store_opening_hours.split(', ')
            
            start_time_1, end_time_1 = store_opening_hours_1.split('-')
            start_time_2, end_time_2 = store_opening_hours_2.split('-')    
        
            if int(start_time_1)<int(today.strftime('%H%M'))<int(end_time_1): is_open = True
            if int(start_time_2)<int(today.strftime('%H%M'))<int(end_time_2): is_open = True          
        '''
        
    return

# Helper function
def is_open_today(store_opening_hours):
    #today = pd.Timestamp.today()
    if len(store_opening_hours) == 9:
        start_time, end_time = store_opening_hours.split('-')    
        if int(start_time)<int(today.strftime('%H%M'))<int(end_time): return True
    elif store_opening_hours == 'Closed': return False
    else:
        store_opening_hours_1, store_opening_hours_2 = store_opening_hours.split(', ')
        
        start_time_1, end_time_1 = store_opening_hours_1.split('-')
        start_time_2, end_time_2 = store_opening_hours_2.split('-')    
    
        if int(start_time_1)<int(today.strftime('%H%M'))<int(end_time_1): return True
        if int(start_time_2)<int(today.strftime('%H%M'))<int(end_time_2): return True 
    return False

def main():
    token_key = 'TOKEN_UTOWN'
    token = os.environ.get(token_key)
    
    updater = Updater(token, use_context=True)

    dp = updater.dispatcher

    buttons = []

    today = pd.Timestamp.today()

    dp.add_handler(CommandHandler("start", start))
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

    dp.add_handler(CommandHandler("open", show_open_stores))

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
