# -*- coding: utf-8 -*-
import os
import qrcode
from PIL import Image

path = os.path.dirname(__file__)
icon_path = os.path.abspath(os.path.join(path, "avatar.png"))
ICON_OBJ = Image.open(icon_path)


def make_qr(url_text):
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=10,
        border=1
    )
    qr.add_data(url_text)
    qr.make(fit=True)
    img = qr.make_image()

    img = img.convert("RGBA")
    img_w, img_h = img.size
    factor = 4
    size_w = int(img_w / factor)
    size_h = int(img_h / factor)

    icon = ICON_OBJ
    icon_w, icon_h = icon.size
    if icon_w > size_w:
        icon_w = size_w
    if icon_h > size_h:
        icon_h = size_h
    icon = icon.resize((icon_w, icon_h), Image.ANTIALIAS)

    w = int((img_w - icon_w) / 2)
    h = int((img_h - icon_h) / 2)
    img.paste(icon, (w, h), icon)
    # img.save("qrcode.png")
    return img

if __name__ == "__main__":
    make_qr('www.baidu.com')
