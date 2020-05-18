# ####################################
# Generate QR Code
import pyqrcode

qr = pyqrcode.create('35804521179642029623961972919942362859427657035910623146181604598373783747941')
token = 'test291857694'
filename = 'static/'+ token+'.png'
qr.png(filename, scale=8)

# ####################################
# Read QR Code
from pyzbar.pyzbar import decode
from PIL import Image

d = decode(Image.open(filename))

print(d[0].data.decode('ascii'))