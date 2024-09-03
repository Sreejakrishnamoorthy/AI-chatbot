import smtplib
import speech_recognition as sr
import pyttsx3
import email
import imaplib
import re
import webbrowser
from time import sleep
import pyautogui as auto
import pyperclip
import mailbox
from email.message import EmailMessage
from flask import *
from flask_sock import Sock
import train_predict
import json

with open('./resources/intents.json') as json_file:
    intents = json.load(json_file)
link = "meet.google.com"
host = 'imap.gmail.com'
username = 'sreejakrishnamoorthy2004@gmail.com'
password = 'sreeja@2004'

response = {
    "text": '',
    "from": ''
}

email_list = {
    'anitha': 'anithaaru00006@gmail.com',
    'lavanya': 'lavsminion15@gmail.com',

}


def talk(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def get_info():
    microphone = sr.Microphone()
    listener = sr.Recognizer()
    with microphone as source:
        print('listening...')
        listener.adjust_for_ambient_noise(source)
        voice = listener.listen(source)
        info = listener.recognize_google(voice)
        return info


def get_info_and_predict():
    microphone = sr.Microphone()
    listener = sr.Recognizer()
    with microphone as source:
        print('listening...')
        listener.adjust_for_ambient_noise(source)
        voice = listener.listen(source)
        info = listener.recognize_google(voice)
        prediction = train_predict.predict(info.lower())
        print(prediction)
        return [info, prediction]


def get_inbox(web_socket):
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(username, password)
    mail.list()
    mail.select('inbox')
    result, data = mail.uid('search', None, "UNSEEN")  # (ALL/UNSEEN)
    i = len(data[0].split())

    for x in range(i):
        latest_email_uid = data[0].split()[x]
        result, email_data = mail.uid('fetch', latest_email_uid, '(RFC822)')
        raw_email = email_data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)

        email_from = str(email.header.make_header(email.header.decode_header(email_message['From'])))
        talk(email_from + 'has sent you a mail')
        response['text'] = email_from + 'has sent you a mail'
        response['from'] = 'bot'
        web_socket.send(str(response))
        email_to = str(email.header.make_header(email.header.decode_header(email_message['To'])))
        # talk(email_to)
        # response['text'] = email_to
        # response['from'] = 'bot'
        # web_socket.send(str(response))
        subject = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))
        talk(subject)
        response['text'] = subject
        response['from'] = 'bot'
        web_socket.send(str(response))

        # Body details
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True)
                talk(body.decode('utf-8'))
                response['text'] = body.decode('utf-8')
                response['from'] = 'bot'
                web_socket.send(str(response))
                regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
                url = re.findall(regex, body.decode('utf-8'))
                if url:
                    talk('Meeting link available. Do you like to join it?')
                    response['text'] = 'Meeting link available. Do you like to join it?'
                    response['from'] = 'bot'
                    web_socket.send(str(response))
                    req = get_info()
                    response['text'] = req
                    response['from'] = 'user'
                    web_socket.send(str(response))
                    if 'yes' in req:
                        for i in url:
                            webbrowser.open(i[0])
                            sleep(10)
                            auto.hotkey('ctrl', 'd')
                            auto.hotkey('ctrl', 'e')
                            sleep(1)
                            auto.click(1329, 588)
                else:
                    continue
            else:
                continue

    start_or_restart(web_socket)


def send_email(receiver, subject, message):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    # Make sure to give app access in your Google account
    server.login('agsvision2022@gmail.com', 'AGSvision2022*')
    email = EmailMessage()
    email['From'] = 'agsvision2022@gmail.com'
    email['To'] = receiver
    email['Subject'] = subject
    email.set_content(message)
    server.send_message(email)


def host_meeting(web_socket):
    webbrowser.open_new_tab('https://' + link)
    sleep(20)
    auto.click(216, 682)
    sleep(5)
    auto.click(225, 689)
    sleep(5)
    auto.click(1145, 628)
    sleep(3)
    talk('Your link has been generated successfully...please wait')
    linktojoin = pyperclip.paste()
    attach_link_to_mail(linktojoin,web_socket)
    start_or_restart(web_socket)


def attach_link_to_mail(linktojoin,web_socket):
    talk('To Whom you want to send email')
    response['text'] = 'To Whom you want to send email'
    response['from'] = 'bot'
    web_socket.send(str(response))
    name = get_info()
    response['text'] = name
    response['from'] = 'user'
    web_socket.send(str(response))
    receiver = email_list[name.lower()]
    print(receiver)
    talk('What is the subject of your email?')
    response['text'] = 'What is the subject of your email?'
    response['from'] = 'bot'
    web_socket.send(str(response))
    subject = get_info()
    response['text'] = subject
    response['from'] = 'user'
    web_socket.send(str(response))
    talk('Tell me the text in your email')
    response['text'] = 'Tell me the text in your email'
    response['from'] = 'bot'
    web_socket.send(str(response))
    message = get_info()
    response['text'] = message
    response['from'] = 'user'
    web_socket.send(str(response))
    message2 = message + " " + linktojoin
    send_email(receiver, subject, message2)
    talk('Your email is sent')
    # talk('Do you want to send more email?')
    # send_more = get_info()
    # print(send_more)
    # if 'yes' in send_more:
    #     attach_link_to_mail(linktojoin)


def get_email_info(web_socket):
    talk('To Whom you want to send email')
    response['text'] = 'To Whom you want to send email'
    response['from'] = 'bot'
    web_socket.send(str(response))
    name = get_info()
    response['text'] = name
    response['from'] = 'user'
    web_socket.send(str(response))
    receiver = email_list[name.lower()]
    print(receiver)
    talk('What is the subject of your email?')
    response['text'] = 'What is the subject of your email?'
    response['from'] = 'bot'
    web_socket.send(str(response))
    subject = get_info()
    response['text'] = subject
    response['from'] = 'user'
    web_socket.send(str(response))
    talk('Tell me the text in your email')
    response['text'] = 'Tell me the text in your email'
    response['from'] = 'bot'
    web_socket.send(str(response))
    message = get_info()
    response['text'] = message
    response['from'] = 'user'
    web_socket.send(str(response))
    send_email(receiver, subject, message)
    talk('Your email is sent')
    response['text'] = 'Your email is sent'
    response['from'] = 'bot'
    web_socket.send(str(response))
    # talk('Do you want to send more email?')
    # response['text'] = 'Do you want to send more email?'
    # response['from'] = 'bot'
    # web_socket.send(str(response))
    # send_more = get_info()
    # response['text'] = send_more
    # response['from'] = 'user'
    # web_socket.send(str(response))
    # print(send_more)
    # if 'yes' in send_more:
    #     get_email_info(web_socket)
    start_or_restart(web_socket)


app = Flask(__name__)
sock = Sock(app)


@sock.route('/start')
def handle_web_socket(web_socket):
    start_or_restart(web_socket)


def start_or_restart(web_socket):
    text = 'Hi, I am vision. What can I do for you ?'
    response['text'] = text
    response['from'] = 'bot'
    talk(text)
    web_socket.send(str(response))
    req = get_info_and_predict()
    print(req)
    response['text'] = req[0]
    response['from'] = 'user'
    web_socket.send(str(response))
    if req is not None and req[1] == 'send':
        get_email_info(web_socket)
    if req is not None and req[1] == 'check':
        get_inbox(web_socket)
    if req is not None and req[1] == 'create':
        host_meeting(web_socket)


@app.route('/')
def main():
    return render_template('sample.html')


if __name__ == '__main__':
    app.run()
