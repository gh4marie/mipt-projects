#!/usr/bin/python3

import config
import telegram
import json
from random import randint

try:
    token_file = open("token.txt", "r")
    token = token_file.readlines()[0]
    token_file.close()
except FileNotFoundError:
    print("ERROR! Failed to open token.txt")
    print("Tip: create token.txt and put your bot's token in it")
    exit()


# Сессия создаётся для каждого, кто пишет что-то боту.
class Session:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.testing = False
        self.test_id = None
        self.correct_ans = None
        
    def begin_test(self, test_id, correct_ans):
        self.testing = True
        self.test_id = test_id
        self.correct_ans = correct_ans
    
    def end_test(self):
        self.testing = False
    
    def check_ans(self, ans):
        return str(self.correct_ans) == str(ans)


# Получает номер последнего обновления
def get_last_update_id(updates):
    id_list = list()
    for update in updates:
        id_list.append(update["update_id"])
    if len(id_list) == 0:
        return 0
    else:
        return max(id_list)


# Очищает обновления, полученные, когда бот был выключен.
def clear_updates(bot):
    last_update_id = get_last_update_id(bot.getUpdates())
    #bot.getUpdates(last_update_id)
    return last_update_id + 1


# Находит сессию в списке по номеру чата. Создаёт новую сессию, если не находит.
def get_session(chat_id, sessions):
    for session in sessions:
        if session.chat_id == chat_id:
            return session
    sessions.append(Session(chat_id))
    return sessions[-1]


# Обрабатывает сообщение
def handle_message(message, sessions):
    message_text = message['text']
    chat_id = message['chat']['id']
    session = get_session(chat_id, sessions)
    
    if session.testing:                                     # Если идёт тестирование
        check_ans(session, message_text)                    # Проверить ответ
        
    elif message_text == "/start":                          # Если отправили /start
        bot.sendMessage(chat_id, config.text_greeting)      # Отправить приветствие
        
    elif message_text == "/test":                           # Если отправили /test
        send_test(session)                                  # Начать тестирование
    
    else:                                                   # Если команда не распознана
        bot.sendMessage(chat_id, config.text_confused)      # Отправить сообщение с предупреждением


# Загружает тесты из файла в tests_dict
def load_tests():
    global tests_dict
    file = open("test.json", "r")
    tests_dict = json.load(file)
    file.close()


# Тестирует пользователя
def send_test(session):
    tests = tests_dict['tests']
    test_id = randint(0, len(tests) - 1)
    test = tests[test_id]
    
    correct_ans = test["correct_ans"]
    incorrect_ans = test["incorrect_ans"]
    all_ans = incorrect_ans + [correct_ans]
    
    bot.sendMessage(session.chat_id, config.text_testing)
    try:
        bot.sendPhoto(session.chat_id, test["img"])
    except telegram.error.BadRequest:
        print("Send test error!", test["img"])
        bot.sendMessage(session.chat_id, config.text_img_error)
        return
        
    correct_ans_num = -1
    for i in range(len(all_ans)):
        ans_id = randint(0, len(all_ans) - 1)
        try:
            bot.sendPhoto(session.chat_id, all_ans[ans_id], caption=str(i + 1))
        except telegram.error.BadRequest:
            print("Send test error!", all_ans[ans_id])
            bot.sendMessage(session.chat_id, config.text_img_error)
            return
        if all_ans[ans_id] == correct_ans:
            correct_ans_num = i + 1
        all_ans.pop(ans_id)

    session.begin_test(test_id, correct_ans_num)


# Проверяет ответ пользователя
def check_ans(session, user_ans):
    tests = tests_dict['tests']
    test = tests[session.test_id]
    
    if session.check_ans(user_ans):
        bot.sendMessage(session.chat_id, config.text_correct)
    else:
        bot.sendMessage(session.chat_id, config.text_wrong % (session.correct_ans))
        try:
            bot.sendPhoto(session.chat_id, test["help_img"])
        except telegram.error.BadRequest:
            print("Send help error!", test["help_img"])
            bot.sendMessage(session.chat_id, config.text_help_error)
            
    session.end_test()


# Запускается при запуске программы
def main():
    print("===STARTING BOT===")

    last_update_id = clear_updates(bot)
    sessions = list()
    while True:
        updates = bot.getUpdates(last_update_id, timeout=100)
        if len(updates) > 0:
            last_update_id = get_last_update_id(updates) + 1
            for update in updates:
                last_message = update["message"]
                if not last_message:
                    continue
                # print(last_message)
                handle_message(last_message, sessions)


# Бот
global bot
bot = telegram.bot.Bot(token)

# Словарь тестов
global tests_dict
load_tests()

# Запуск бота
main()

"""
markup = telegram.ReplyKeyboardMarkup(
    keyboard=['/start']
)
recognize = {
    '/start': [bot.sendMessage, "Hello \n I can test your skill of recognizing nmr spectra \U0001F604"
                                          " \n Firstly, a spectrum of proton magnetic resonance and four variants of molecules will be sent to you. You are to choose a suitable picture and type its number.\n If your answer is wrong, I'll send the correct answer with explanation."],
 #   'Stop': [exit, None]
}
"""
