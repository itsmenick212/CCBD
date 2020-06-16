"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages orders for flowers.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'OrderFlowers' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""
import math
import dateutil.parser
import datetime
import boto3
import time
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def validate_restaurant_booking(name, location, cuisine, diningTime, numberOfPeople, phoneNumber):
    locations = ['new york', 'maryland', 'chicago', 'buffalo']
    if location is not None and location.lower() not in locations:
        return build_validation_result(False,
                                       'Location',
                                       'We do not have {}, would you prefer a different location?  '
                                       'Our most popular location is New York'.format(location))

    cuisines = ['italian', 'chinese', 'indian', 'thai', 'korean', 'burmese']
    if cuisine is not None and cuisine.lower() not in cuisines:
        return build_validation_result(False,
                                       'Cuisine',
                                       'We do not have {}, would you prefer a different cuisine?  '
                                       'Our most popular cuisine is Indian'.format(cuisine))


    totalNumbers = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    if numberOfPeople is not None and numberOfPeople not in totalNumbers:
        return build_validation_result(False,
                                       'numberOfPeople',
                                       'We cannot accomodate {}, would you please change the number of people?'
                                       'I can make a booking of upto 10 people'.format(numberOfPeople))


    # if date is not None:
    #     if not isvalid_date(date):
    #         return build_validation_result(False, 'PickupDate', 'I did not understand that, what date would you like to pick the flowers up?')
    #     elif datetime.datetime.strptime(date, '%Y-%m-%d').date() <= datetime.date.today():
    #         return build_validation_result(False, 'PickupDate', 'You can pick up the flowers from tomorrow onwards.  What day would you like to pick them up?')

    if diningTime is not None:
        if len(diningTime) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

        hour, minute = diningTime.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

        if hour < 10 or hour > 22:
            # Outside of business hours
            return build_validation_result(False, 'DiningTime', 'Restaurants can only be booked between 10:00 to 22:00 hours. Can you specify a time during this range?')

    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """


def book_restaurant(intent_request):
    """
    Performs dialog management and fulfillment for booking restaurants.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """

    name = get_slots(intent_request)["Name"]
    cuisine = get_slots(intent_request)["Cuisine"]
    location = get_slots(intent_request)["Location"]
    diningTime = get_slots(intent_request)["DiningTime"]
    numberOfPeople = get_slots(intent_request)["NumberOfPeople"]
    phoneNumber = get_slots(intent_request)["PhoneNumber"]
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_restaurant_booking(name, location, cuisine, diningTime, numberOfPeople, phoneNumber)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        # Pass the price of the flowers back through session attributes to be used in various prompts defined
        # on the bot model.
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        # if flower_type is not None:
        #     output_session_attributes['Price'] = len(flower_type) * 5  # Elegant pricing model

        output_session_attributes['Prices'] = 100

        return delegate(output_session_attributes, get_slots(intent_request))

    # Order the flowers, and rely on the goodbye message of the bot to define the message to the end user.
    # In a real bot, this would likely involve a call to a backend service.

    # Get the service resource
    sqs = boto3.resource('sqs')

    # Get the queue
    queue = sqs.get_queue_by_name(QueueName='sqs')

    # Create a new message
    response = queue.send_message(MessageBody='boto3', MessageAttributes={
        'slots': {
            'Name': name,
            'Location': location,
            'Cuisine': cuisine,
            'DiningTime': diningTime,
            'NumberOfPeople': numberOfPeople,
            'PhoneNumber': phoneNumber
        }
    })

    logger.log(response)

    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Thanks, a {} restaurant in {} for {} people has been booked under the name {} and phone number {} for {}'.format(cuisine, location, numberOfPeople, name, phoneNumber, diningTime)})


""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']


    # Dispatch to your bot's intent handlers
    if intent_name == "WhatIsYourName":
        return book_restaurant(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
