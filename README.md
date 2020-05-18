# Beam Wallet - Digital Wallet

Web Programming with Python and JavaScript

## Welcome to Beam Wallet

**Beam Wallet** is a digital wallet soultion developed on **Django** framework for merchants and customers. **Beam Wallet** securely stores users' payment information and passwords, allows users to store funds, make transactions, and track payment histories. By using **Beam Wallet**, customers can complete purchases from their selected merchants easily and quickly, as well as receive funds or remittances from friends and family globally. For merchants, they can accept customers payment with their qrcode after connected with customers, payment transcations are also being recorded.

## App Features

- **Sign up**: sign up Beam Wallet with a username, password, email and phone number. An activition token will be generated together with the **Email verification** and sent to the email address. A **private key** will be generated for the user and it will be used when authenicate transcations. This private key will automatically be **encrypted** before being stored to the database by *Fernet symmetric encryption*. A QRCode will be generated using *pyqrcode* for the use of merchant payment.

- **login**: each login requires **SMS verification** to secure identity of the user. **SMS** service is provided by *Twilio*. When user recieves the activation code in SMS, type the code and login.

- **Register banks**: customers can choose their banks and setup connection with Beam Wallet by just 1 click. 

- **Top up**: after customers' wallet is connected to bank. Customers now can top up their wallet from their selected bank and get ready to use their wallet. Each Top up process are secured by authenicating and verifying both Beam Wallet **(wallet API Key issued by bank)** and customer **(bank private key, bank user ID)** identities to the bank. After indentities being verified, fund will be transferred. Bank returns successful status and transcation ID in JSON format to Beam Wallet. 

- **Build contact list**: user allows to add other Beam Wallet users to their contact list. A **shared key** will be generate by both users private keys and public keys. This shared key will be hold by both users and will be used as **digital signature** when they send funds to each other. An **email notification** will be send to both users to inform this new connection.

- **Transfer fund to contact**: send and recieve fund in Beam Wallet is easy. Just choose a contact in user's contact list and enter the amount. *Elliptic-Curve Diffie-Hellman (ECDH) Key Exchange* method will be used to verified both user's identities and connection. Their shared key will be used as **digital signature** for the transcation. Fund will be transferred to the receiptant after verification is successfully. **Email notification** will be sent to both users.

- **Choose Merchant**: user can view the list of Merchants in Beam Wallet and added them to his/her Merchant list.

- **Payment to Merchant by QRCode**: a **QRCode** is stored in user wallet. User can show the qrcode to Mechant to scan payment.

- **Scan payment from customers**: merchants are able to choose a customer from their customer list. The **QRCode** of that users will show on the next steps and merchant can enter the amount charged and reference for scanning. If scanner device is connect with Beam Wallet, info. from the QRCode will be read by scanner. For this project, there is no scanner device used. A *Scan Button* will imitate the scanner action. **QRCode** carries the identity information of the user. After scan, the user information will be verifed before the payment transcation processed. An **Email noification** will send to customer. 

- **Dashboard**: both Merchant and customer will have unique dashboard to display useful information of their wallet, such as functions, balance, top up transcation histories, payment histories, merchant list, contact list.

- **View transcation History**: Transcation histories for Top up , fund transfer (send and recieve), merchant payment will be kept and show on user dashboard

- **Spending Analysis**: A simple **spending analysis** base on user activities on Top up, send and recieve funds, pay merchant, will be presented in **Donut Chart** using *C3.js*. Such that, user can have glance on their spending behavior.

## Security Features:
- Fernet symmetric encryption : encrypted important data and store in database
- Elliptic-Curve cryptography : produce private key, public key and shared key to verify identities
- Elliptic-Curve Diffie-Hellman (ECDH) Key Exchange : digital signature for transcations
- SMS Authenication by Twilio : verify user identities when login Beam Wallet

## Summary on Functions functionality

**twofa App**
- views.py : functions for user registration, SMS authenication, email notification, account activation and login
- decorators.py : check if user is authenciated before login to wallet
- forms.py : create registration form and SMS token verification form
- managers.py : Add user registration information onto the User Model
- tokens.py : create an activiation token for the use of account activation via email
- CSS/style.css : contains css and mobile responsive design for homepage, registeration page and SMS token verification page

**phone_verification App**
- forms.py : create and validate country code and phone number in registeration form
- view.py : functions for validate the SMS token which sent to user when user tries to login

**wallet App**
- views.py : functions for add bank, Top up account, add contact list, fund transfer, add merchant, send merchant payment, generate and validate private key,public key, shared key , retrieve data to display on dashboard, prepare spending analysis date and pass it to C3 donut Chart API
- dashboard1.js : to generate Donunt Chart, using Jquery to call django function passing API data in JSON format to the chart
- other .js : for menu and slide bar menu activities
- style1.css : contains css and mobile responsive design for dashboard and html pages related to the functions

**bank app**
- views.py : imiate bank account withdrawal function, return data in JSON format

## Youtube Demo

https://youtu.be/KksTeFMq53A

## Pre-requisites and programs used versions

-  Python 3.6 or higher
-  the latest version of pip

## Setting up the development environment

1. git clone this project

2. Run **pip3 install -r requirements.txt** in your terminal window to make sure that all of the necessary Python packages are installed.

3. Run **python3 manage.py makemigrations** to make sure the models are uptodate for using

4. Run **python3 manage.py migrate** for migration

5. Run **python3 manage.py runserver** to start up this Django application.

## Visiting an URL and interact with the application

- Open the localhost http://127.0.0.1:8000/ to run the app
- Signup 2 customer accounts to add bank, top up fund,add contact, pay merchant
- make sure provide valid email address and phone number for authenication use

## Admin Function

- To visit the **Django Admin**, login to http://127.0.0.1:8000/admin
- Username1 : admin4 Password : admin4

## Developer Setup

- Beam Wallet is intergated the **Twilio** SMS authenication

1. Make sure to register for a **Twilio** Account.
2. Setup an Account Security app via the Twilio Console.
3. Copy an **Production API Key** from the Dashboard and paste it in .env

- Email SMTP host server setting for email authenitication

*Gmail is being used as the host in this project,please use different setting if you use different host*
1. EMAIL_HOST = 'smtp.gmail.com'
2. EMAIL_HOST_USER = 'your email address'
3. EMAIL_HOST_PASSWORD = 'your password'
4. EMAIL_PORT = 587

## Author : Cheryl Kwong  Email : cherylkwong@gmail.com
## Project developed by : Python, Django, Javascript, Jquery, bootstrap, CSS, HTML, SQLite3
