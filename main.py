import os

import qrcode


def create_qr_code(text, file_name):
    img = qrcode.make(text)
    img.save(file_name)


def remove_file(path):
    os.remove(path)
