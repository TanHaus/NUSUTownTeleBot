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
    update.message.reply_text("<b> Welcome to the NUS UTown TeleBot! </b> \n\n" +
    "This Bot aims to provide information about the shops and amenities available in the UTown Campus.\n\n" +
    "To enhance your UTown experience, you may find the following commands useful: \n" +
    "/stores: UTown directory\n"
    "/open: Shops currently open\n"
    "/haze: Haze conditions in UTown\n\n"
    "<b>Disclaimer</b>: The opening hours reported by this bot are not applicable during Public Holidays and School Holidays.\n", parse_mode = 'html')

def show_stores(update, context):
    keyboard = []
    for i in categories:
        keyboard.append([InlineKeyboardButton(i, callback_data=i)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Select Category', reply_markup = reply_markup)

    return 'handle_category'

def show_open_stores(update, context):
    today = get_current_SGtime()
    open_stores = ''
    for index in opening_hours.index:
        store_opening_hours = opening_hours.loc[index, today.strftime('%a')]
        if is_open_today(store_opening_hours) and store_opening_hours != 'Open':
            close_time = get_close_time(index)
            open_stores += '- {} (until <b>{}</b>)\n'.format(opening_hours.loc[index, 'Store'], close_time)

    str247_stores = open247_stores[0]
    for store in open247_stores[1:]:
        str247_stores = str247_stores + ', ' + store
    
    open_stores += '- {}: <b>Open 24/7</b> 🏪'.format(str247_stores)

    update.message.reply_text('The following stores/amenities are still open:\n{}'.format(open_stores), parse_mode='html')

def haze(update, context):
    haze_message = update.message.reply_text('Getting data from Singapore\'s public data...')
    try:
        PSI = get_SG_data('PSI')
        PM25 = get_SG_data('PM2.5')
    except:
        haze_message.edit_text('There is an error getting data from Singapore\'s public data 🙁\nPlease try again later!')
    else:
        descriptor = ''
        if 0 <= PSI <= 50: descriptor = 'Good'
        elif PSI <= 100: descriptor = 'Moderate'
        elif PSI <= 200: descriptor = 'Unhealthy'
        elif PSI <= 300: descriptor = 'Very unhealthy'
        else: descriptor = 'Hazardous'

        if PSI == None: PSI == 'NA'
        if PM25 == None: PM25 == 'NA'
        haze_message.edit_text('PSI reading in UTown: {}\nPM2.5 reading in UTown: {}μ/m³\n\nStatus: {}'.format(PSI, PM25, descriptor))

        if descriptor in ['Unhealthy', 'Very unhealthy']: update.message.reply_text('Please minimize outdoor activities! ❌🏃')
        elif descriptor == 'Hazardous': update.message.reply_text('Please avoid all outdoor activities. Visit NEA for further instructions\n\nhttps://www.haze.gov.sg/')

def weather(update, context):
    weather_message = update.message.reply_text('Getting data from Singapore\'s public data...')
    today = get_current_SGtime()
    date = today.strftime('%A - %d %b, %Y')
    try:
        temp = get_SG_data('temperature')
        humidity = get_SG_data('humidity')
        forecast = get_SG_data('weather forecast')
    except:
        weather_message.edit_text('There is an error getting data from Singapore\'s public data 🙁\nPlease try again later!')
    else:
        if temp == None: temp = 'NA'
        if humidity == None: humidity = 'NA'
        if forecast == None: forecast = 'NA'
        weather_message.edit_text('<b>{}</b> at UTown\n\nTemperature (°C): {} 🌡️\nHumidity (%): {} 💧\nForecast: {}'.format(date, temp, humidity, forecast), parse_mode='html')

##########################
#                        #
#    Handler functions   #
#                        #
##########################

def handle_category(update, context):
    query = update.callback_query
    query.message.edit_text("Selected Category: {}".format(query.data))

    keyboard = []
    for i in opening_hours[opening_hours['Category']==query.data]['Store']:
        keyboard.append([InlineKeyboardButton(i, callback_data=i)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if query.data == 'Food & Beverages' or query.data == 'Retail':
        query.message.reply_text('Select Store', reply_markup = reply_markup)
    else: 
        query.message.reply_text('Select Amenity', reply_markup = reply_markup)

    return 'handle_store'

def handle_store(update, context):
    today = get_current_SGtime()
    query = update.callback_query
    store_opening_hours = get_opening_hours(query.data, today)

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
            store_opening_hours_next = get_opening_hours(query.data, next_day)

            while(store_opening_hours_next == 'Closed'):
                next_day = next_day + dt.timedelta(days=1)
                store_opening_hours_next = get_opening_hours(query.data, next_day)
                tomorrow = False
        
            if tomorrow: 
                next_day_text = 'tomorrow'
            else:
                next_day_text = 'on ' + next_day.strftime('%A')
        
        return 'But you can still visit {} {} from {} 😊'.format(query.data, next_day_text, store_opening_hours_next)

    
    info = '<b>{}</b> {}\n'.format(query.data, get_sub_category(query.data))
    if get_category(query.data) == 'Food & Beverages': 
        info += 'Halal Certified\n' if is_halal(query.data) else 'Not Halal Certified\n'
    info += 'Located in: {}\n\n'.format(get_location(query.data))

    if query.data in open247_stores: info += 'Opening hours: Open 24/7 🏪\n'
    else:
        info += 'Opening status: '
        if store_opening_hours == 'Closed': info += 'Closed right now. {}\n\n'.format(when_store_open())
        elif is_open_today(store_opening_hours):
            index = opening_hours[opening_hours.Store == query.data].index[0]
            info += "Open (until <b>{}</b>)\n\n".format(get_close_time(index))
        else: info += 'Closed right now. {}\n\n'.format(when_store_open())
        
        info += 'Opening hours:\n'
        for day_in_week in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
            hours = opening_hours[opening_hours.Store == query.data][day_in_week].iloc[0]
            info += '    {}{}: {}\n'.format(day_in_week, ' (today)' if day_in_week == today.strftime('%a') else '', hours)

    keyboard = [[InlineKeyboardButton("Show on Google Maps", url=opening_hours[opening_hours.Store == query.data].iloc[0]["Maps"])]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.edit_text(info, parse_mode='html', reply_markup = reply_markup)

    return None

def error(update, context):
    print('There is an error!\n{}'.format(context.error))

##########################
#                        #
#    Helper functions    #
#                        #
##########################

def get_opening_hours(store, date):
    store_info = opening_hours[opening_hours.Store==store]
    if is_PH(date) and store_info['PH'].iloc[0] != 'As usual':
        store_opening_hours = store_info['PH'].iloc[0]
    else:
        store_opening_hours = store_info[date.strftime('%a')].iloc[0]

    return store_opening_hours

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

    elif store_opening_hours == 'Closed':
        return False

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

def get_close_time(index):
    '''
    Get closing time those in the format of 'HHMM-HHMM' and 'HHMM-HHMM, HHMM-HHMM'
    '''
    close_time = ''
    today = get_current_SGtime()
    store_opening_hours = opening_hours.loc[index, today.strftime('%a')]
    next_day = today + dt.timedelta(days=1)

    if len(store_opening_hours) == 9:
        if store_opening_hours.split('-')[-1] == '2359': 
            store_opening_hours_next = opening_hours.loc[index, next_day.strftime('%a')]
            close_time = store_opening_hours_next[5:9]
        else:
            close_time = store_opening_hours.split('-')[-1]
    
    else:
        store_opening_hours_1, store_opening_hours_2 = store_opening_hours.split(', ') 
        end_time_1 = store_opening_hours_1.split('-')[-1]
        end_time_2 = store_opening_hours_2.split('-')[-1]
    
        if int(today.strftime('%H%M'))<int(end_time_1): 
            close_time = end_time_1
        else:
            if end_time_2 == '2359': 
                store_opening_hours_next = opening_hours.loc[index, next_day.strftime('%a')]
                close_time = store_opening_hours_next[5:9]
            else:
                close_time = end_time_2

    return close_time

def get_location(store):
    store_info = opening_hours[opening_hours.Store==store]
    return store_info['Location'].iloc[0]

def is_halal(store):
    store_info = opening_hours[opening_hours.Store==store]
    halal = store_info['Halal Certified'].iloc[0]
    if halal == 'Yes': return True
    return False

def get_category(store):
    store_info = opening_hours[opening_hours.Store==store]
    return store_info['Category'].iloc[0]

def get_sub_category(store):
    store_info = opening_hours[opening_hours.Store==store]
    if store_info['Sub-Category'].iloc[0] == '-':
        return ''
    else:
        return "- " + store_info['Sub-Category'].iloc[0]

def get_current_SGtime():
    '''
    Return the current time in Singapore UTC+08:00
    '''
    return dt.datetime.now(tz=dt.timezone(dt.timedelta(hours=8)))

def get_SG_data(element):
    '''
    Get Singapore public data from https://data.gov.sg/

    Accepted arguments: psi, pm2.5, temperature, rainfall, humidity, wind direction, wind speed, weather forecast
    '''

    element = element.lower()
    data_types = {'psi': 'environment/psi',
                  'pm2.5': 'environment/pm25',
                  'temperature': 'environment/air-temperature',
                  'rainfall': 'environment/rainfall',
                  'humidity': 'environment/relative-humidity',
                  'wind direction': 'environment/wind-direction',
                  'wind speed': 'environment/wind-speed',
                  'weather forecast': 'environment/2-hour-weather-forecast'}
    if element not in data_types.keys(): return None

    URL = 'https://api.data.gov.sg/v1/' + data_types[element]
    
    today = get_current_SGtime()
    DATE_TIME = today.strftime('%Y-%m-%dT%H:%M:%S')
    PARAMS = {'date_time': DATE_TIME}

    response = requests.get(url = URL, params = PARAMS).json()
    data = response['items'][0]

    if element == 'psi': return data['readings']['psi_twenty_four_hourly']['south']

    elif element == 'pm2.5': return data['readings']['pm25_one_hourly']['south']

    elif element in ['temperature', 'rainfall', 'humidity', 'wind direction', 'wind speed']:
        stations = {x['station_id']: x['value'] for x in data['readings']}
        ids = ['S50', 'S60', 'S116', 'S115']
        for id in ids:
            if stations.get(id) == None: continue
            else: return stations[id]
        return None

    elif element == 'weather forecast': 
        areas = {x['area']: x['forecast'] for x in data['forecasts']}
        return areas['Queenstown']

    return None

def get_PH():
    '''
    Get a list of Public holidays in Singapore from Ministry of Manpower https://www.mom.gov.sg/
    '''
    response = requests.get(url='https://www.mom.gov.sg/-/media/mom/documents/employment-practices/public-holidays/public-holidays-sg-2020.ics')
    raw = response.text
    events = raw.split('BEGIN:VEVENT\r\n')[1:]
    PH = {}
    for event in events:
        index_date = event.find('DTSTART')
        date = event[index_date+19: index_date+27]
        name_i = event.find('SUMMARY')
        name_f = event.find('END:VEVENT')
        name = event[name_i+8: name_f-2]
        PH[date] = name
    return PH

def is_PH(date):
    '''
    Check if the given date is a public holiday

    Accept both a string 'YYYYMMDD' and a datetime object
    '''
    if isinstance(date, str) and (date in public_holidays): return True
    if isinstance(date, dt.datetime) and (date.strftime('%Y%m%d') in public_holidays): return True

    return False
 
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
        fallbacks=[CommandHandler('stores', show_stores)]
    )

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("open", show_open_stores))
    dp.add_handler(CommandHandler("haze", haze))
    dp.add_handler(CommandHandler("weather", weather))
    dp.add_handler(conv_handler)
    dp.add_error_handler(error)

    port = os.environ.get('PORT', 'None')
    if port!='None':
        updater.start_webhook(listen='0.0.0.0',
                            port=int(port),
                            url_path=token)
        updater.bot.set_webhook("https://nus-utown.herokuapp.com/{}".format(token))
    else:
        updater.start_polling()

    updater.idle()

if __name__=='__main__':
    # Create Pandas Dataframe
    opening_hours = pd.read_excel('Utown Outlets Opening Hours.xlsx',
                                  header=0, index_col=False, keep_default_na=True)
                                  
    categories = opening_hours['Category'].unique()
    stores = opening_hours['Store']
    public_holidays = get_PH()
    open247_stores = opening_hours[opening_hours['Mon']=='Open']['Store'].tolist()

    main()
