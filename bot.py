import os
import logging
from datetime import datetime, timedelta
from uuid import uuid4

import requests
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ParseMode, TelegramError
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext, CallbackQueryHandler,
)
from main import create_qr_code, remove_file

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Loading env file
load_dotenv('.env')

API_KEY = os.getenv('UTIL_API_KEY')

GENDER, PHOTO, LOCATION, BIO, SELECT_TYPE, PIN, DISTRICT_RESULT, PIN_RESULT, RESTART, QR_CODE_TEXT_INPUT, PIN_INPUT = range(
    11)


# Conversation Start
def start(update: Update, _: CallbackContext) -> int:
    reply_keyboard = [['/qrcode']]
    if os.getenv('API_KEY') == 'production':
        requests.get('https://api.countapi.xyz/hit/namespace/rahulreghunathmannady')
    user = update.message.from_user
    logger.info("User %s Started the conversation.", user.first_name)
    update.message.reply_text(
        'Hi☺️ \nMy name is blablabla.\n'
        '/qrcode to create a custom qr code',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return SELECT_TYPE


def qr_code_response(update: Update, _: CallbackContext) -> int:
    """
    Read the district if success ask for date
    """
    file_name = f'{uuid4()}.png'
    create_qr_code(update.message.text, file_name)
    try:
        update.message.reply_photo(
            photo=open(file_name, 'rb')
        )
    except TelegramError:
        pass
    remove_file(file_name)


def qr_code_text_dialogue(update: Update, _: CallbackContext) -> int:
    """
    Select the input option
    """

    update.message.reply_text(
        'Enter your text',
        reply_markup=ReplyKeyboardRemove(),
    )
    return QR_CODE_TEXT_INPUT


def cancel(update: Update, _: CallbackContext) -> int:
    """
    End the conversation
    """
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day. Stay safe 😁', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(API_KEY)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('restart', start)],
        states={
            SELECT_TYPE: [MessageHandler(
                Filters.regex('^(/qrcode)$'),
                qr_code_text_dialogue
            )],
            QR_CODE_TEXT_INPUT: [MessageHandler(Filters.regex('^[a-zA-Z ]+$'), qr_code_response)],
        },
        allow_reentry=True,
        fallbacks=[CommandHandler('stop', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
