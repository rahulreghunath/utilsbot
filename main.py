import os

import qrcode


def create_qr_code(text, file_name):
    img = qrcode.make(text)
    print(type(img))  # qrcode.image.pil.PilImage
    img.save(file_name)


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
def remove_file(path):
    os.remove(path)
