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
        if is_open_today(store_opening_hours) and store_opening_hours != 'Open':
            close_time = get_close_time(store_opening_hours)
            open_stores += '- {} until <b>{}</b>\n'.format(opening_hours.loc[index, 'Store'], close_time)
    open_stores += '- {}: open 24/7'.format(get_247_stores(opening_hours))
    update.message.reply_text('The following stores are still open:\n{}'.format(open_stores), parse_mode='html')

def haze(update, context):
    update.message.reply_text('Getting data from Singapore\'s public data...')
    try:
        PSI = get_SG_data('PSI')
        PM25 = get_SG_data('PM2.5')
    except:
        update.message.reply_text('There is an error getting data from Singapore\'s public data 🙁')
        update.message.reply_text('Please try again later!')
    else:
        update.message.reply_text('PSI reading in UTown: {}'.format(PSI))
        update.message.reply_text('PM2.5 reading in UTown: {}'.format(PM25))

def weather(update, context):
    update.message.reply_text('Getting data from Singapore\'s public data...')
    try:
        temp = get_SG_data('temperature')
        humidity = get_SG_data('humidity')
    except:
        update.message.reply_text('There is an error getting data from Singapore public data 🙁')
        update.message.reply_text('Please try again later!')
    else:
        update.message.reply_text('Temperature: {}°C 🌡️\nHumidity: {}% 💧'.format(temp, humidity))


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
        next_day_text = 'later'
        store_opening_hours_next = store_opening_hours
        
        if len(store_opening_hours) == 9 and int(today.strftime('%H%M')) < int(store_opening_hours.split('-')[0]):
            None

        elif len(store_opening_hours) == 20 and int(today.strftime('%H%M')) < int(store_opening_hours.split(', ')[-1].split('-')[0]):
            store_opening_hours_next = store_opening_hours.split(', ')[-1]

        else:
            tomorrow = True
            next_day = today + dt.timedelta(days=1)
            store_opening_hours_next = opening_hours[opening_hours.Store==query.data]['Term Opening Hours (' + next_day.strftime('%a') + ')'].iloc[0]

            while(store_opening_hours_next == 'Closed'):
                next_day = next_day + dt.timedelta(days=1)
                store_opening_hours_next = opening_hours[opening_hours.Store==query.data]['Term Opening Hours (' + next_day.strftime('%a') + ')'].iloc[0]
                tomorrow = False
        
            if tomorrow: 
                next_day_text = 'tomorrow'
            else:
                next_day_text = 'on ' + next_day.strftime('%A')
        
        query.message.reply_text('But you can still visit {} {} from {} 😊'.format(query.data, next_day_text, store_opening_hours_next))

    if store_opening_hours == 'Closed':
        query.message.reply_text("{} is closed".format(query.data))
        when_store_open()

    elif store_opening_hours == 'Open':
        query.message.reply_text("{} is open".format(query.data))
        query.message.reply_text('Opening hours: 24/7')

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
    
    elif store_opening_hours == 'Open':
        return True

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
    Get Singapore public data from https://data.gov.sg/
    '''

    element = element.lower()
    data_types = {'psi': 'environment/psi',
                  'pm2.5': 'environment/pm25',
                  'temperature': 'environment/air-temperature',
                  'rainfall': 'environment/rainfall',
                  'humidity': 'environment/relative-humidity',
                  'wind direction': 'environment/wind-direction',
                  'wind speed': 'environment/wind-speed'}
    
    URL = 'https://api.data.gov.sg/v1/' + data_types[element]
    station_id = 'S50'                          # station S50 is at Clementi Road
    
    today = get_current_SGtime()
    DATE_TIME = today.strftime('%Y-%m-%dT%H:%M:%S')
    PARAMS = {'date_time': DATE_TIME}

    response = requests.get(url = URL, params = PARAMS).json()
    readings = response['items'][0]['readings']

    if element == 'psi': return readings['psi_twenty_four_hourly']['south']

    elif element == 'pm2.5': return readings['pm25_one_hourly']['south']

    elif element in ['temperature', 'rainfall', 'humidity', 'wind direction', 'wind speed']:
        stations = {x['station_id']: x['value'] for x in readings}
        return stations[station_id]

    return None

def get_247_stores(opening_hours):
    open247_stores = opening_hours[opening_hours['Term Opening Hours (Mon)']=='Open']['Store'].to_numpy()
    open247_stores_str = ''
    for store in open247_stores:
        if open247_stores_str == '':
            open247_stores_str += store
        open247_stores_str = open247_stores_str + ', ' + store
    return open247_stores_str

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
    dp.add_handler(CommandHandler("weather", weather))
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
