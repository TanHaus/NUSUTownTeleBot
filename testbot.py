import os
import requests
import datetime as dt
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import pandas as pd


##########################
#                        #
#   Command functions    #
#                        #
##########################

def start(update, context):
    update.message.reply_text("Welcome to the NUS Utown TeleBot!\n" +
    "Ever been hungry in the middle of the night and dying to know which food stores are still open? " +
    "Or wondered to know what are the retail and sporting options here in Utown?\n" 
    "Then you have come to the right place. Created by TanHaus, this Bot aims to provide useful information about the shops and amenities available in the Utown Campus. " +
    "To help you enhance your Utown experience, you may find the following commands useful:\n" +
    "/stores: Shows the directory of Utown shops and amenities."
    "\n/open: Shows all stores that are currently open."
    "\n/temp: Shows current air temperature.")

def show_stores(update, context):
    keyboard = []
    for i in categories:
        keyboard.append([InlineKeyboardButton(i, callback_data=i)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose a category', reply_markup = reply_markup)

    return 'handle_category'

def show_open_stores(update, context):
    today = get_current_SGtime()
    open_stores = ''
    column_label_today = 'Term Opening Hours (' + today.strftime('%a') + ')'
    for index in opening_hours.index:
        store_opening_hours = opening_hours.loc[index, column_label_today]
        if is_open_today(store_opening_hours):
            close_time = get_close_time(store_opening_hours)
            open_stores += '- {} until <b>{}</b>\n'.format(opening_hours.loc[index, 'Store'], close_time)

    update.message.reply_text('The following stores are still open:\n{}'.format(open_stores), parse_mode='html')

def haze(update, context):
    PSI = get_SG_data('PSI')['psi_twenty_four_hourly']['south']
    PM25 = get_SG_data('PM2.5')['pm25_one_hourly']['south']
    update.message.reply_text('PSI reading in UTown: {}'.format(PSI))
    update.message.reply_text('PM2.5 reading in UTown: {}'.format(PM25))


##########################
#                        #
#    Handler functions   #
#                        #
##########################

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
    today = get_current_SGtime()
    query = update.callback_query
    store_opening_hours = opening_hours[opening_hours.Store==query.data]['Term Opening Hours (' + today.strftime('%a') + ')'].iloc[0]
    
    def when_store_open():
        tomorrow = True
        next_day = today + dt.timedelta(days=1)
        store_opening_hours_next = opening_hours[opening_hours.Store==query.data]['Term Opening Hours (' + next_day.strftime('%a') + ')'].iloc[0]
        while(store_opening_hours_next == 'Closed'):
            next_day = next_day + dt.timedelta(days=1)
            store_opening_hours_next = opening_hours[opening_hours.Store==query.data]['Term Opening Hours (' + next_day.strftime('%a') + ')'].iloc[0]
            tomorrow = False
        
        text = 'tomorrow'
        if tomorrow == False: text = 'on ' + next_day.strftime('%A')

        query.message.reply_text('But you can still visit {} {} from {} 😊'.format(query.data, text, store_opening_hours_next))

    if store_opening_hours == 'Closed':
        query.message.reply_text("{} is closed".format(query.data))
        when_store_open()

    elif is_open_today(store_opening_hours):
        query.message.reply_text("{} is open".format(query.data))
        query.message.reply_text('Opening hours: {}'.format(store_opening_hours))

    else:
        query.message.reply_text("{} is closed".format(query.data))
        when_store_open()
        
    return
    

##########################
#                        #
#    Helper functions    #
#                        #
##########################

def is_open_today(store_opening_hours):
    '''
    Check if the input store_opening_hours is open right now. Return a boolean

    Format for parameter: HHMM-HHMM. Also handle 'Closed' and 'HHMM-HHMM, HHMM-HHMM'
    '''

    today = get_current_SGtime()
    
    if len(store_opening_hours) == 9:
        start_time, end_time = store_opening_hours.split('-')    
        
        if end_time == '2359':
            if int(start_time)<=int(today.strftime('%H%M'))<=int(end_time): return True
        else:
            if int(start_time)<=int(today.strftime('%H%M'))<int(end_time): return True
    
    else:
        store_opening_hours_1, store_opening_hours_2 = store_opening_hours.split(', ')
        
        start_time_1, end_time_1 = store_opening_hours_1.split('-')
        start_time_2, end_time_2 = store_opening_hours_2.split('-')    
    
        if int(start_time_1)<=int(today.strftime('%H%M'))<int(end_time_1): return True

        if end_time_2 == '2359':
            if int(start_time_2)<=int(today.strftime('%H%M'))<=int(end_time_2): return True 
        else:
            if int(start_time_2)<=int(today.strftime('%H%M'))<int(end_time_2): return True 
    
    return False

def get_close_time(store_opening_hours):
    '''
    Get closing time those in the format of 'HHMM-HHMM' and 'HHMM-HHMM, HHMM-HHMM'
    '''

    if len(store_opening_hours) == 9:
        close_time = store_opening_hours.split('-')[-1]
        if close_time == '2359': return 'midnight'
        return close_time
    
    else:
        today = get_current_SGtime()
        store_opening_hours_1, store_opening_hours_2 = store_opening_hours.split(', ')
        
        start_time_1, end_time_1 = store_opening_hours_1.split('-')
    
        if int(start_time_1)<=int(today.strftime('%H%M'))<int(end_time_1): return end_time_1

        end_time_2 = store_opening_hours_2.split('-')[-1]
        if end_time_2 == '2359': return 'midnight'
        return end_time_2

def get_current_SGtime():
    '''
    Return the current time in Singapore UTC+08:00
    '''

    return dt.datetime.now(tz=dt.timezone(dt.timedelta(hours=8)))

def get_SG_data(element):
    '''
    Get data from data.gov.sg
    '''

    SG_data_URLs = {'PSI': 'https://api.data.gov.sg/v1/environment/psi',
                    'PM2.5': 'https://api.data.gov.sg/v1/environment/pm25'}
    
    today = get_current_SGtime()
    DATE_TIME = today.strftime('%Y-%m-%dT%H:%M:%S')

    URL = SG_data_URLs[element]
    PARAMS = {'date_time': DATE_TIME}

    return requests.get(url = URL, params = PARAMS).json()['items'][0]['readings']

##########################
#                        #
#      Main program      #
#                        #
##########################

def main():
    token_key = 'TOKEN_UTOWN'
    token = os.environ.get(token_key)
    
    updater = Updater(token, use_context=True)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('stores', show_stores)],
        states={
            'handle_category': [CallbackQueryHandler(handle_category)],
            'handle_store': [CallbackQueryHandler(handle_store)]
        },
        fallbacks=[CommandHandler("stores", show_stores)]
    )

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("open", show_open_stores))
    dp.add_handler(CommandHandler("haze", haze))
    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__=='__main__':
    # Create Pandas Dataframe
    opening_hours = pd.read_excel('Utown Outlets Opening Hours.xlsx',
                                  header=0, index_col=False, keep_default_na=True)
    categories = opening_hours['Category'].unique()
    stores = opening_hours['Store']

    main()
