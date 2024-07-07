from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import sqlite3

# DB connection
sqlConnection = sqlite3.connect("where_do_you_sit.db", check_same_thread=False)
cursor = sqlConnection.cursor()

TOKEN: Final = '6741923286:AAGCRPIa1Xu1Wu72Ey4mrsXTf6fgik73K58'
BOT_USERNAME: Final = '@gdzie_siedzisz_w_samolocie_bot'

# Planes data
length = 50
columns = 6

def initialize_db():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id INTEGER,
            row INTEGER,
            column INTEGER,
            occupant TEXT,
            FOREIGN KEY(flight_id) REFERENCES flights(id)
        )
    ''')
    
    sqlConnection.commit()

def initialize_aircraft(flight_id):
    for row in range(length):
        for col in range(columns):
            cursor.execute('''
                INSERT INTO seats (flight_id, row, column, occupant) 
                VALUES (?, ?, ?, ?)
            ''', (flight_id, row, col, '-'))
    sqlConnection.commit()

# Commands
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Siemka! Wyślij mi swoje miejsce, a ja cię nałożę na mapkę samolotu')

async def list_flights_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute('SELECT name FROM flights')
    flights_list = cursor.fetchall()
    flights_list_text = "\n".join([flight[0] for flight in flights_list])
    await update.message.reply_text(f'Dostępne loty:\n{flights_list_text}')

async def add_flight_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.full_name == "Dawid Lipowczan":
        try:
            flight_name = context.args[0]
            cursor.execute('INSERT INTO flights (name) VALUES (?)', (flight_name,))
            flight_id = cursor.lastrowid
            initialize_aircraft(flight_id)
            await update.message.reply_text(f'Lot {flight_name} został dodany.')
        except IndexError:
            await update.message.reply_text('Podaj nazwę lotu, np. /add_flight Lot123')
        except sqlite3.IntegrityError:
            await update.message.reply_text('Lot o takiej nazwie już istnieje.')
    else:
        await update.message.reply_text('Tylko Dawid Lipowczan może dodawać loty.')

async def remove_flight_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.full_name == "Dawid Lipowczan":
        try:
            flight_name = context.args[0]
            cursor.execute('DELETE FROM flights WHERE name = ?', (flight_name,))
            await update.message.reply_text(f'Lot {flight_name} został usunięty.')
            sqlConnection.commit()
        except IndexError:
            await update.message.reply_text('Podaj nazwę lotu, np. /remove_flight Lot123')

async def show_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = show_status(context.args[0])
    await update.message.reply_text(message)

def show_status(flight_name):
    cursor.execute('SELECT id FROM flights WHERE name = ?', (flight_name,))
    flight = cursor.fetchone()
    if not flight:
        return f"Lot {flight_name} nie istnieje."
    
    flight_id = flight[0]
    cursor.execute('SELECT row, column, occupant FROM seats WHERE flight_id = ? ORDER BY row, column', (flight_id,))
    seats = cursor.fetchall()
    
    aircraft_string = ""
    current_row = -1
    for seat in seats:
        row, column, occupant = seat
        if row != current_row:
            if current_row != -1:
                aircraft_string += "\n"
            current_row = row
            aircraft_string += str(row + 1) + '('
        if column == 3:
            aircraft_string += '   '
        aircraft_string += occupant + ' '
    
    aircraft_string += "\n               \\_/ //\n_.-''-.._.-''-.._.. -(||)(')\n                             '''"
    return aircraft_string

async def send_async_message(update, message):
    await update.message.reply_text(message)

def handle_response(text: str, user, update):
    parts = text.split()
    if len(parts) < 3:
        return "Nieprawidłowy format. Użyj formatu 'nazwa_lotu numer litera', np. 'Lot123 18 d'. Jeżeli chcesz się usunąć z tego lotu wyślij 'Lot123 0 0'"

    flight_name, row_str, seat_str = parts
    cursor.execute('SELECT id FROM flights WHERE name = ?', (flight_name,))
    flight = cursor.fetchone()
    if not flight:
        return f"Lot {flight_name} nie istnieje."

    flight_id = flight[0]
    place_to_sit_row = int(row_str) - 1
    place_to_sit_letter = ord(seat_str.lower()) - ord('a')

    if place_to_sit_row < 0:
        cursor.execute('''
            UPDATE seats SET occupant = '-' 
            WHERE flight_id = ? AND occupant = ?
        ''', (flight_id, f"{user.first_name} {user.last_name[:3]}"))
        sqlConnection.commit()
        return show_status(flight_name)

    cursor.execute('''
        SELECT occupant FROM seats WHERE flight_id = ? AND row = ? AND column = ?
    ''', (flight_id, place_to_sit_row, place_to_sit_letter))
    occupant = cursor.fetchone()[0]

    if occupant != "-":
        message = 'Upsi, tutaj już ktoś siedzi, ale jak wyślesz tą wiadomość jeszcze 10 razy to może uda ci się mnie przechytrzyć :)'
        asyncio.create_task(send_async_message(update, message))
        return show_status(flight_name)
    
    cursor.execute('''
        UPDATE seats SET occupant = '-' 
        WHERE flight_id = ? AND occupant = ?
    ''', (flight_id, f"{user.first_name} {user.last_name[:3]}"))
    
    cursor.execute('''
        UPDATE seats SET occupant = ? 
        WHERE flight_id = ? AND row = ? AND column = ?
    ''', (f"{user.first_name} {user.last_name[:3]}", flight_id, place_to_sit_row, place_to_sit_letter))
    
    sqlConnection.commit()
    return show_status(flight_name)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text
    user: str = update.message.chat
    print(f'User ({user.id}) in {message_type}: "{text}"') 

    response: str = handle_response(text, user, update)
    print('Bot:', response)
    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Prawdopodobnie podałeś swój numer w złym formacie: numerlotu + spacja + litera od a do f np. Lot123 18 d')
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting bot')
    initialize_db()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('list_flights', list_flights_command))
    app.add_handler(CommandHandler('add_flight', add_flight_command))
    app.add_handler(CommandHandler('remove_flight', remove_flight_command))
    app.add_handler(CommandHandler('show_status', show_status_command))

    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    app.add_error_handler(error)

    print('Polling...')
    app.run_polling(poll_interval=1)
