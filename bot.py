import logging
import os
from uuid import uuid4
from PIL import Image
from io import BytesIO
import validators
import requests
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, TelegramError
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext
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

INSTAGRAM_URL, SELECT_TYPE, RESTART, COMPRESSION_RATE, QR_CODE_TEXT_INPUT, COMPRESSION_IMAGE, PIN_INPUT, IMAGE_TO_COMPRESS = range(
    8)


# Conversation Start
def start(update: Update, _: CallbackContext) -> int:
    reply_keyboard = [['/qrcode', '/compress']]
    user = update.message.from_user
    logger.info("User %s Started the conversation.", user.first_name)
    update.message.reply_text(
        'Hello☺️\n'
        '/qrcode to create a custom qr code\n'
        '/compress to compress image\n',
        # '/instagram to download instagram photos & videos',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return SELECT_TYPE


def qr_code_text_dialogue(update: Update, _: CallbackContext) -> int:
    """
    Select the input option
    """

    update.message.reply_text(
        'Enter your text',
        reply_markup=ReplyKeyboardRemove(),
    )
    return QR_CODE_TEXT_INPUT


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

    return SELECT_TYPE


def image_compression_get_image(update: Update, _: CallbackContext) -> int:
    """
    Read the district if success ask for date
    """
    file = update.message.photo[-1].get_file()
    image = Image.open(requests.get(file.file_path, stream=True).raw)
    compressed = BytesIO()
    compressed.name = f'compressed_{file.file_path.split("/")[-1]}'
    global IMAGE_TO_COMPRESS
    IMAGE_TO_COMPRESS = {'image': image, 'compressed': compressed}

    update.message.reply_text(
        'Enter compression rate out of 100',
        reply_markup=ReplyKeyboardRemove(),
    )
    return COMPRESSION_RATE


def compress_image_dialogue(update: Update, _: CallbackContext) -> int:
    """
    Select the input option
    """

    update.message.reply_text(
        'Send image to compress',
        reply_markup=ReplyKeyboardRemove(),
    )
    return COMPRESSION_IMAGE


def compressed_image_response(update: Update, _: CallbackContext) -> int:
    """
    Select the input option
    """
    IMAGE_TO_COMPRESS['image'].save(IMAGE_TO_COMPRESS['compressed'], optimize=True, quality=int(update.message.text))
    IMAGE_TO_COMPRESS['compressed'].seek(0)
    update.message.reply_photo(
        photo=IMAGE_TO_COMPRESS['compressed']
    )
    return SELECT_TYPE


def insta_url_dialogue(update: Update, _: CallbackContext) -> int:
    """
    Select the input option
    """

    update.message.reply_text(
        'Send url to download',
        reply_markup=ReplyKeyboardRemove(),
    )
    return INSTAGRAM_URL


def instagram_download_response(update: Update, _: CallbackContext) -> int:
    if validators.url(update.message.text):
        headers = {
            'Accept-Language': 'IN',
            'Accept': 'application/json',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        }
        # Getting data
        data = requests.get(
            f'{update.message.text}&__a=1',
            headers=headers
        )
        if data.status_code == 200:
            # results = data.json()
            print(data.text)
        #     if 'edge_sidecar_to_children' in results:
        #         for node in results['edge_sidecar_to_children']['edges']:
        #             if not node['node']['is_video']:
        #                 update.message.reply_photo(node['node']['display_url'])
        #             else:
        #                 update.message.reply_video(node['node']['video_url'])
        #     else:
        #         if not results['is_video']:
        #             update.message.reply_photo(results['display_url'])
        #         else:
        #             update.message.reply_video(results['video_url'])
        #     return SELECT_TYPE
        # else:
        #     update.message.reply_text(
        #         'Server busy. Please try after some time',
        #         reply_markup=ReplyKeyboardRemove(),
        #     )
        # update.message.reply_text(
        #     'Something went wrong. Please try after some time',
        #     reply_markup=ReplyKeyboardRemove(),
        # )
    else:
        update.message.reply_text(
            'Enter correct url',
            reply_markup=ReplyKeyboardRemove(),
        )
    return INSTAGRAM_URL


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
            SELECT_TYPE: [
                MessageHandler(
                    Filters.regex('^(/qrcode)$'),
                    qr_code_text_dialogue
                ),
                MessageHandler(
                    Filters.regex('^(/compress)$'),
                    compress_image_dialogue
                ), MessageHandler(
                    Filters.regex('^(/instagram)$'),
                    insta_url_dialogue
                )],
            QR_CODE_TEXT_INPUT: [MessageHandler(Filters.text, qr_code_response)],
            COMPRESSION_IMAGE: [MessageHandler(Filters.photo, image_compression_get_image)],
            COMPRESSION_RATE: [MessageHandler(Filters.regex('^[1-9][0-9]?$|^100$'), compressed_image_response)],
            INSTAGRAM_URL: [MessageHandler(Filters.all, instagram_download_response)],
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
