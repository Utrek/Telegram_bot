import random
import telebot
import sqlalchemy
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from telebot import types, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from сonfig import TOKEN, DSN
from models import create_tables, Users, Words, Added_words, Deleted_words



state_storage = StateMemoryStorage()

bot = telebot.TeleBot(TOKEN,state_storage=state_storage)


engine = sqlalchemy.create_engine(DSN)

create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()


known_users = []
userStep = {}
buttons = []


def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"

def add_base_words():
    words_dict = {'i':'я', 'you':'вы', 'he':'он', 'she':'она', 'it':'оно', 'they':'они', 'we':'мы', 
         'green':'зеленый', 'yellow':'жёлтый', 'blue':'синий', 'orange':'оранжевый', 'red':'красный',
         'cat':'кошка', 'dog':'собака', 'fish':'рыба','fly':'муха','mole':'крот'}
    for word in words_dict:
        words = session.query(Words.english_word).filter(Words.english_word == word).all()
        if not words:
            session.add(Words(english_word =word,russian_word=words_dict[word]))
            session.commit()
    return 'готово'


def show_count(id):
    count_words = session.query(func.count(Words.english_word)).scalar()
    count_add_words = session.query(func.count(Added_words.id).filter(Added_words.user_id== id)).scalar()
    count_del_words = session.query(func.count(Deleted_words.id).filter(Deleted_words.user_id == id)).scalar()
    count = count_words + count_add_words - count_del_words
    return count

def get_id(name):
    id = session.query(Users.id).filter(Users.user_name == name).all()
    return id[0][0]
def get_target_words_dict(id):
    target_words = {}
    add_base_words
    base_words = session.query(Words.english_word, Words.russian_word).all()
    for en_word, ru_word in base_words:
        target_words[en_word] = ru_word
    add_words = session.query(Added_words.english_word,Added_words.russian_word).filter(Added_words.user_id == id).all()
    if add_words:
        for en_word,ru_word in add_words:
            target_words[en_word] = ru_word
    del_words = session.query(Deleted_words.english_word).filter(Deleted_words.user_id == id).all()
    if del_words:
        for en_word in del_words:
            if en_word[0] in target_words:
                target_words.pop(en_word[0])
    return target_words


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово ➖'
    NEXT = 'Дальше ➡'
    LESSON = 'Начать изучение 📚'
    EXIT = 'Выйти 🚪'
    BACK = '⬅ Назад'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        known_users.append(uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0


@bot.message_handler(commands=['start'])
def hello(message):
    cid = message.chat.id
    if cid not in known_users:
        known_users.append(cid)
        userStep[cid] = 0
    name = message.from_user.username
    user_table_name = session.query(Users.user_name).filter_by(user_name=name).all()
    if user_table_name:
        bot.send_message(cid, f'Привет, {name}! \nЯ бот для изучения английского языка.\n Чтобы начать нажми кнопку: \nНачать изучение 📚 \n У тебя есть возможность использовать тренажёр, как конструктор, и собирать свою собственную базу для обучения.\n Для этого воспрользуйся инструментами:\n Добавить слово ➕, \n Удалить слово ➖. \n Тренировки можешь проходить в удобном для себя темпе.')
    else:
       session.add(Users(user_name=name))
       session.commit()
       bot.send_message(cid, f'Привет, {name}! \nЯ бот для изучения английского языка.\n Чтобы начать нажми кнопку: \nНачать изучение 📚 \n У тебя есть возможность использовать тренажёр, как конструктор, и собирать свою собственную базу для обучения.\n Для этого воспрользуйся инструментами:\n Добавить слово ➕, \n Удалить слово ➖. \n Тренировки можешь проходить в удобном для себя темпе.')
    start(message)


@bot.message_handler(commands=['go'])
def start(message):
    add_base_words()
    greeting = 'Выбери действие'
    markup = types.ReplyKeyboardMarkup(row_width=2)
    yes = types.KeyboardButton(Command.LESSON)
    no = types.KeyboardButton(Command.EXIT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    markup.add(yes, no, add_word_btn, delete_word_btn)
    bot.send_message(message.chat.id,greeting,reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == Command.EXIT)
def exit(message):
    bot.send_message(message.chat.id, 'Спасибо за использование бота!')
    bot.stop_polling()

@bot.message_handler(func=lambda message: message.text == Command.LESSON)
def create_cards(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    name = message.from_user.username
    id = get_id(name)
    
    target_words = get_target_words_dict(id)

    global buttons
    buttons = []
    
    target_word = random.choice(list(target_words))
    translate = target_words[target_word]
    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)
    others = random.sample(list(target_words), 3)
    if target_word in others:
        others.remove(target_word)
        others.append(random.choice(list(target_words)))
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)

@bot.message_handler(func=lambda message: message.text == Command.BACK)
def back(message):
    start(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def del_english_word(message):
    bot.send_message(message.from_user.id, 'Введи слово на английском.')
    bot.register_next_step_handler(message,del_check)
def del_check(message):
    global del_eng_word
    del_eng_word = message.text
    name = message.from_user.username
    id = get_id(name)
    base_word = session.query(Words.english_word).filter(Words.english_word == del_eng_word.lower()).all()
    add_word = session.query(Added_words.english_word).filter(Added_words.english_word == del_eng_word.lower(),Added_words.user_id == id).all()
    if del_eng_word != 'Удалить слово ➖' and del_eng_word != 'Добавить слово ➕' and del_eng_word !='Начать изучение 📚' and del_eng_word !='Выйти 🚪':
        if base_word:
            bot.send_message(message.from_user.id, "А теперь на русском!")
            bot.register_next_step_handler(message,del_base)
        elif add_word:
            del_word = session.query(Added_words).filter(Added_words.english_word == del_eng_word.lower(),Added_words.user_id == id).one()
            session.delete(del_word)
            session.commit()
            bot.send_message(message.from_user.id, f'Готово – {del_eng_word} удалено!')
        else:
            bot.send_message(message.from_user.id,'Такого слова нет!')
    elif del_eng_word == "Выйти 🚪":
        start(message)
    else:
         del_english_word(message) 
       
def del_base(message):
    del_rus_word = message.text
    name = message.from_user.username
    id = get_id(name)
    session.add(Deleted_words(english_word= del_eng_word.lower(), russian_word=del_rus_word.lower(),user_id=id))
    session.commit()
    bot.send_message(message.chat.id, f'Готово – {del_eng_word} удалено!')
    
        

@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_english_word(message):
    bot.send_message(message.from_user.id, 'Введи слово на английском!') 
    bot.register_next_step_handler(message,add_russian_word)
def add_russian_word(message):
    global eng_word
    eng_word = message.text
    name = message.from_user.username
    id = get_id(name)
    base_word = session.query(Words.english_word).filter(Words.english_word == eng_word.lower()).all()
    add_word = session.query(Added_words.english_word).filter(Added_words.english_word == eng_word.lower(),Added_words.user_id == id).all()
    del_word = session.query(Deleted_words.english_word).filter(Deleted_words.english_word == eng_word.lower(),Deleted_words.user_id == id).all()
    if eng_word != 'Удалить слово ➖' and eng_word != 'Добавить слово ➕' and eng_word !='Начать изучение 📚' and eng_word !='Выйти 🚪':
        if base_word:
            if del_word:
                delete = session.query(Deleted_words).filter(Deleted_words.english_word == eng_word.lower(),Deleted_words.user_id == id).one()
                session.delete(delete)
                session.commit()
                count = show_count(id) 
                bot.send_message(message.from_user.id, f'Готово – {eng_word} добавлено!\nСлов для изучения- {count}')
            else:
                count = show_count(id) 
                bot.send_message(message.from_user.id, f'Ты уже учишь это! \nСлов для изучения- {count}')
        elif add_word:
            count = show_count(id)
            bot.send_message(message.from_user.id, f'Ты уже учишь это! \nСлов для изучения- {count}')
        else:
            bot.send_message(message.from_user.id, "А теперь на русском!")
            bot.register_next_step_handler(message,add_base)
    elif eng_word == "Выйти 🚪":
        start(message)
    else:
         add_english_word(message) 
    
def add_base(message):
    rus_word = message.text.lower()
    name = message.from_user.username
    id = get_id(name)    
    session.add(Added_words(english_word= eng_word.lower(), russian_word=rus_word.lower(),user_id=id))
    session.commit()
    count = show_count(id)

    bot.send_message(message.chat.id, f'✅ Готово!\nТеперь слов для изучения - {count}')


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично! 🔥", hint]
            hint = show_hint(*hint_text)
            bot.send_message(message.from_user.id, hint)
            menu(message)
        elif '⛔' in text:
            hint = ['Всё ещё неверно!']
            bot.send_message(message.from_user.id, hint,reply_markup=markup)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '⛔'
            markup.add(*buttons)
            hint = show_hint("Неправильно! Попробуй ещё раз.\n"
                             f"Переведи на английский 🇷🇺{data['translate_word']}")
            bot.send_message(message.chat.id, hint, reply_markup=markup)
def menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    next_btn = types.KeyboardButton(Command.NEXT)
    back_btn = types.KeyboardButton(Command.BACK)
    markup.add(back_btn,next_btn)
    bot.send_message(message.chat.id, 'Выбери действие', reply_markup=markup)


bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling(skip_pending=True)

if __name__ == '__main__':
    print('Бот запущен...')
    bot.polling(none_stop=True)


