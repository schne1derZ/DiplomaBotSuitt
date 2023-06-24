from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, state
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3 as sq
import logging
import hashlib
from sqlite3 import IntegrityError, OperationalError
import re
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import MessageToDeleteNotFound
from aiogram.utils.callback_data import CallbackData

from aiogram.dispatcher import filters

#API_TOKEN = '6277595590:AAGTrcUyez8gRZjDdDWI9YFLMRWn_sqFO3k'
API_TOKEN = '5967970543:AAHKVIixFYcN4huWMMgyqJfHHKqrK3gx0Os'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

db = sq.connect("EventBottest.sqlite")
cur = db.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS Specialization (
                        id_spec INTEGER NOT NULL UNIQUE,
                        name TEXT NOT NULL UNIQUE,
                        points INTEGER NOT NULL,
                        PRIMARY KEY(id_spec AUTOINCREMENT)
                    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS Student (
                        id_student INTEGER NOT NULL UNIQUE,
                        StudentNumber TEXT NOT NULL UNIQUE,
                        FirstName TEXT NOT NULL,
                        LastName TEXT NOT NULL,
                        Password TEXT NOT NULL,
                        points INTEGER,
                        id_spec INTEGER,
                        Contact TEXT,
                        PRIMARY KEY(id_student AUTOINCREMENT),
                        FOREIGN KEY(id_spec) REFERENCES Specialization(id_spec)
                    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS Teacher (
                    id_teacher INTEGER NOT NULL UNIQUE,
                    FirstName TEXT NOT NULL,
                    LastName TEXT NOT NULL,
                    Username TEXT NOT NULL,
                    Password TEXT NOT NULL,
                    Description TEXT,
                    ContactData TEXT NOT NULL,
                    PRIMARY KEY(id_teacher AUTOINCREMENT)
                    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS teacher_spec_tkl (
                    id_spec_teacher INTEGER NOT NULL,
                    id_teacher_spec INTEGER NOT NULL,
                    PRIMARY KEY(id_teacher_spec,id_spec_teacher),
                    FOREIGN KEY(id_teacher_spec) REFERENCES Teacher(id_teacher)
                    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS Source (
                    id_source INTEGER NOT NULL UNIQUE,
                    link TEXT NOT NULL,
                    description TEXT,
                    data TEXT NOT NULL,
                    company TEXT NOT NULL,
                    PRIMARY KEY(id_source AUTOINCREMENT)
                    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS source_special_tkl (
                    id_source_spec INTEGER NOT NULL,
                    id_spec_source INTEGER NOT NULL,
                    PRIMARY KEY(id_source_spec,id_spec_source),
                    FOREIGN KEY(id_source_spec) REFERENCES Source(id_source)
                    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS FAQ (
                    id_faq INTEGER NOT NULL UNIQUE,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    PRIMARY KEY(id_faq AUTOINCREMENT)
                )''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        answer TEXT NOT NULL,
        points INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        FOREIGN KEY (question_id) REFERENCES questions (id)
    )
''')
db.commit()
class user:
    def __init__(self, studentNumber='', status='', username=''):
        self.studentNumber = studentNumber
        self.status = status
        self.username = username
User = user("")

class Form(StatesGroup):
    name_student = State()
    specialization = State()
    name_teacher = State()
    specialization_student = State()
    edit_data_cabinet = State()
message_ids = []



@dp.callback_query_handler(lambda c: c.data == 'teachers_info')
async def process_callback_teachers_info(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Show all teachers", callback_data="show_all_teachers"))
    keyboard.add(InlineKeyboardButton("Search by name", callback_data="search_by_name"))
    keyboard.add(InlineKeyboardButton("Search by specialization", callback_data="search_by_spec"))
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Choose an option:", reply_markup=keyboard)

current_page = 0

@dp.callback_query_handler(lambda c: c.data == 'show_all_teachers')
async def process_callback_show_all_teachers(callback_query: types.CallbackQuery):
    global current_page
    current_page = 0
    offset = current_page * 5
    cur.execute(f"SELECT * FROM Teacher LIMIT 5 OFFSET {offset}")
    teachers = cur.fetchall()
    keyboard = InlineKeyboardMarkup(row_width=1)
    for teacher in teachers:
        keyboard.add(InlineKeyboardButton(f"{teacher[1]} {teacher[2]}", callback_data=f"teacher_info:{teacher[0]}"))
    keyboard.add(InlineKeyboardButton("Next", callback_data="next_page"))
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="All teachers:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'next_page')
async def process_callback_next_page(callback_query: types.CallbackQuery):
    global current_page
    current_page += 1
    offset = current_page * 5
    cur.execute(f"SELECT * FROM Teacher LIMIT 5 OFFSET {offset}")
    teachers = cur.fetchall()
    if not teachers:
        current_page -= 1
        await bot.answer_callback_query(callback_query.id, text="No more teachers to display.")
        return
    keyboard = InlineKeyboardMarkup(row_width=1)
    for teacher in teachers:
        keyboard.add(InlineKeyboardButton(f"{teacher[1]} {teacher[2]}", callback_data=f"teacher_info:{teacher[0]}"))
    keyboard.add(InlineKeyboardButton("Previous", callback_data="previous_page"))
    keyboard.add(InlineKeyboardButton("Next", callback_data="next_page"))
    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text="All teachers:", reply_markup=keyboard)
@dp.callback_query_handler(lambda c: c.data == 'previous_page')
async def process_callback_previous_page(callback_query: types.CallbackQuery):
    global current_page
    if current_page == 0:
        await bot.answer_callback_query(callback_query.id, text="You are already on the first page.")
        return
    current_page -= 1
    offset = current_page * 5
    cur.execute(f"SELECT * FROM Teacher LIMIT 5 OFFSET {offset}")
    teachers = cur.fetchall()
    keyboard = InlineKeyboardMarkup(row_width=1)
    for teacher in teachers:
        keyboard.add(InlineKeyboardButton(f"{teacher[1]} {teacher[2]}", callback_data=f"teacher_info:{teacher[0]}"))
    keyboard.add(InlineKeyboardButton("Previous", callback_data="previous_page"))
    keyboard.add(InlineKeyboardButton("Next", callback_data="next_page"))
    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text="All teachers:", reply_markup=keyboard)
@dp.callback_query_handler(lambda c: c.data == 'search_by_name')
async def process_callback_search_by_name(callback_query: types.CallbackQuery):
    await Form.name_teacher.set()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Enter the teacher's name:")

@dp.message_handler(state=Form.name_teacher)
async def process_name_teacher(message: types.Message, state: FSMContext):
    name = message.text
    cur.execute("SELECT * FROM Teacher WHERE FirstName LIKE ? OR LastName LIKE ?", (f"%{name}%", f"%{name}%"))
    teachers = cur.fetchall()
    keyboard = InlineKeyboardMarkup(row_width=1)
    for teacher in teachers:
        keyboard.add(InlineKeyboardButton(f"{teacher[1]} {teacher[2]}", callback_data=f"teacher_info:{teacher[0]}"))
    await state.finish()
    await bot.send_message(chat_id=message.chat.id, text=f"Teachers with the name '{name}':", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('teacher_info'))
async def process_callback_teacher_info(callback_query: types.CallbackQuery):
    teacher_id = int(callback_query.data.split(':')[1])
    cur.execute("SELECT * FROM Teacher WHERE id_teacher=?", (teacher_id,))
    teacher = cur.fetchone()
    text = f"First Name: {teacher[1]}\nLast Name: {teacher[2]}\nUsername: {teacher[3]}\nDescription: {teacher[5]}\nContact Data: {teacher[6]}"
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(chat_id=callback_query.message.chat.id, text=text)

@dp.callback_query_handler(lambda c: c.data == 'search_by_spec')
async def process_callback_search_by_spec(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Please enter the specialization of the teacher you want to search for:\nBackend\nFrontend\nQA\nData Science\nProject Manager")
    await Form.specialization.set()

@dp.message_handler(state=Form.specialization)
async def process_spec(message: types.Message, state: FSMContext):
    specialization = message.text
    cur.execute(
        "SELECT id_teacher, FirstName, LastName, Description, ContactData FROM Teacher JOIN teacher_spec_tkl ON Teacher.id_teacher = teacher_spec_tkl.id_teacher_spec JOIN Specialization ON teacher_spec_tkl.id_spec_teacher = Specialization.id_spec WHERE Specialization.name = ?",
        (specialization,))
    teachers = cur.fetchall()
    if teachers:
        await bot.send_message(chat_id=message.chat.id, text="Here are the teachers with the specialization " + specialization + ":")
        for teacher in teachers:
            result = f"\nFirst Name: {teacher[1]}\nLast Name: {teacher[2]}\n"
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("Show data", callback_data=f"teacher_info:{teacher[0]}"))
            await bot.send_message(chat_id=message.chat.id, text=result, reply_markup=keyboard)
    else:
        await bot.send_message(chat_id=message.chat.id, text="No teachers found with the specialization " + specialization)
    await state.finish()



@dp.callback_query_handler(lambda c: c.data == 'students_info')
async def process_callback_students_info(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Show all students", callback_data="show_all_students"))
    keyboard.add(InlineKeyboardButton("Search by name", callback_data="search_by_name_stud"))
    keyboard.add(InlineKeyboardButton("Search by specialization", callback_data="search_by_spec_stud"))
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Choose an option:", reply_markup=keyboard)

current_page_stud = 0

@dp.callback_query_handler(lambda c: c.data == 'show_all_students')
async def process_callback_show_all_students(callback_query: types.CallbackQuery):
    global current_page_stud
    current_page_stud = 0
    offset = current_page_stud * 5
    cur.execute(f"SELECT * FROM Student LIMIT 5 OFFSET {offset}")
    students = cur.fetchall()
    keyboard = InlineKeyboardMarkup(row_width=1)
    for student in students:
        keyboard.add(InlineKeyboardButton(f"{student[2]} {student[3]}", callback_data=f"student_info:{student[0]}"))
    keyboard.add(InlineKeyboardButton("Next", callback_data="next_page_stud"))
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="All students:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'next_page_stud')
async def process_callback_next_page_stud(callback_query: types.CallbackQuery):
    global current_page_stud
    current_page_stud += 1
    offset = current_page_stud * 5
    cur.execute(f"SELECT * FROM Student LIMIT 5 OFFSET {offset}")
    students = cur.fetchall()
    if not students:
        current_page_stud -= 1
        await bot.answer_callback_query(callback_query.id, text="No more students to display.")
        return
    keyboard = InlineKeyboardMarkup(row_width=1)
    for student in students:
        keyboard.add(InlineKeyboardButton(f"{student[2]} {student[3]}", callback_data=f"student_info:{student[0]}"))
    keyboard.add(InlineKeyboardButton("Previous", callback_data="previous_page_stud"))
    keyboard.add(InlineKeyboardButton("Next", callback_data="next_page_stud"))
    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text="All students:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'previous_page_stud')
async def process_callback_previous_page_stud(callback_query: types.CallbackQuery):
    global current_page_stud
    if current_page_stud == 0:
        await bot.answer_callback_query(callback_query.id, text="You are already on the first page.")
        return
    current_page_stud -= 1
    offset = current_page_stud * 5
    cur.execute(f"SELECT * FROM Student LIMIT 5 OFFSET {offset}")
    students = cur.fetchall()
    keyboard = InlineKeyboardMarkup(row_width=1)
    for student in students:
        keyboard.add(InlineKeyboardButton(f"{student[2]} {student[3]}", callback_data=f"student_info:{student[0]}"))
    keyboard.add(InlineKeyboardButton("Previous", callback_data="previous_page_stud"))
    keyboard.add(InlineKeyboardButton("Next", callback_data="next_page_stud"))
    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text="All students:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'search_by_name_stud')
async def process_callback_search_by_name_stud(callback_query: types.CallbackQuery):
    await Form.name_student.set()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Enter the student's name:")

@dp.message_handler(state=Form.name_student)
async def process_name_student(message: types.Message, state: FSMContext):
    name = message.text
    cur.execute("SELECT * FROM Student WHERE FirstName LIKE ? OR LastName LIKE ?", (f"%{name}%", f"%{name}%"))
    students = cur.fetchall()
    keyboard = InlineKeyboardMarkup(row_width=1)
    for student in students:
        keyboard.add(InlineKeyboardButton(f"{student[2]} {student[3]}", callback_data=f"student_info:{student[0]}"))
    await state.finish()
    await bot.send_message(chat_id=message.chat.id, text=f"Students with the name '{name}':", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('student_info'))
async def process_callback_student_info(callback_query: types.CallbackQuery):
    student_id = int(callback_query.data.split(':')[1])
    cur.execute("SELECT * FROM Student WHERE id_student=?", (student_id,))
    student = cur.fetchone()
    text = f"First Name: {student[2]}\nLast Name: {student[3]}"
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(chat_id=callback_query.message.chat.id, text=text)


@dp.callback_query_handler(lambda c: c.data == 'search_by_spec_stud')
async def process_callback_search_by_spec_stud(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Please enter the specialization of the student you want to search for:\n1-Backend\n2-Frontend\n3-Data Science\n4-Project Manager\n5-QA")
    await Form.specialization_student.set()

@dp.message_handler(state=Form.specialization_student)
async def process_spec_stud(message: types.Message, state: FSMContext):
    specialization = message.text
    cur.execute(
        "SELECT id_student, FirstName, LastName FROM Student JOIN Specialization ON Student.id_spec = Specialization.id_spec WHERE Specialization.name = ?",
        (specialization,))
    students = cur.fetchall()
    if students:
        await bot.send_message(chat_id=message.chat.id, text="Here are the students with the specialization " + specialization + ":")
        for student in students:
            result = f"\nFirst Name: {student[1]}\nLast Name: {student[2]}\n"
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("Show data", callback_data=f"student_info:{student[0]}"))
            await bot.send_message(chat_id=message.chat.id, text=result, reply_markup=keyboard)
    else:
        await bot.send_message(chat_id=message.chat.id, text="No students found with the specialization " + specialization)
    await state.finish()




@dp.message_handler(Command("start"))
async def start_cmd(message: types.Message):
    if User.studentNumber == '' and User.username == '':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Registration", callback_data="register"))
        keyboard.add(types.InlineKeyboardButton("Login", callback_data="login"))
        await message.answer("Welcome! Please choose an option:", reply_markup=keyboard)
    else:
        await message.answer("Sorry, you need to exit for using /start")

@dp.callback_query_handler(text="register")
async def register_callback(callback_query: CallbackQuery, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup()
    await callback_query.answer()
    await callback_query.message.answer("Please enter your student number:")
    await state.set_state("student_number")


@dp.message_handler(state="student_number")
async def student_number_cmd(message: types.Message, state: FSMContext):
    student_number = message.text
    await state.update_data(student_number=student_number)
    await message.answer("Please enter your password:")
    await state.set_state("password")

@dp.message_handler(state="Student_Number")
async def student_number_cmd(message: types.Message, state: FSMContext):
    student_number = message.text
    await state.update_data(student_number=student_number)


@dp.message_handler(state="first_name")
async def first_name_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    student_number = data.get("student_number")
    password = data.get("password")
    first_name = message.text
    await state.update_data(first_name=first_name)
    await message.answer("Please enter your last name:")
    await state.set_state("last_name")

@dp.message_handler(state="last_name")
async def last_name_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    student_number = data.get("student_number")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = message.text
    try:
        cur.execute(
            "INSERT INTO Student (StudentNumber, FirstName, LastName, Password,points) VALUES (?, ?, ?, ?,0)",
            (student_number, first_name, last_name, password)
        )
        db.commit()
    except IntegrityError:
        await message.answer("A student with this student number already exists.")
        await state.finish()
        return
    except OperationalError as e:
        await message.answer(f"An error occurred while inserting data into the database: {e}")
        await state.finish()
        return

    cur.execute(
        "SELECT * FROM Student WHERE StudentNumber=?",
        (student_number,)
    )
    User.studentNumber = student_number
    user_data = cur.fetchone()
    if user_data:
        response = f"Registration successful! Here is your information:\n\n"
        response += f"Student Number: {user_data[1]}\n"
        response += f"First Name: {user_data[2]}\n"
        response += f"Last Name: {user_data[3]}\n"
        await message.answer(response)
        keyboard = InlineKeyboardMarkup()
        login_button = InlineKeyboardButton(text="Login", callback_data="login")
        keyboard.add(login_button)
        delete_button = InlineKeyboardButton(text="cancel registration", callback_data="cancel_registration")
        keyboard.add(delete_button)
        await message.answer("Click the button below to login or cancel registration:", reply_markup=keyboard)
    else:
        await message.answer("An error occurred while retrieving your information from the database.")
    await state.finish()

@dp.callback_query_handler(text="cancel_registration", state="*")
async def cancel_registration_callback(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cur.execute("DELETE FROM Student WHERE StudentNumber=?", (User.studentNumber,))
    db.commit()
    await state.finish()
    await query.message.edit_text(f"{User.studentNumber}")
    User.studentNumber = ""


@dp.callback_query_handler(lambda c: c.data == "login")
async def login_callback(query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=2)
    teacher_button = InlineKeyboardButton("as Teacher", callback_data="login_teacher")
    student_button = InlineKeyboardButton("as Student", callback_data="login_student")
    keyboard.add(teacher_button, student_button)
    await query.message.edit_text("Please choose an option:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'login_teacher')
async def process_callback_login_teacher(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Please enter your username:")
    await dp.current_state(chat=callback_query.from_user.id).set_state("username")

@dp.message_handler(state="username")
async def username_cmd(message: types.Message, state: FSMContext):
    username = message.text
    await state.update_data(username=username)
    await message.answer("Please enter your password:")
    await state.set_state("password_teacher")


@dp.message_handler(state="password_teacher")
async def password_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    username = data.get("username")
    password = message.text
    # Hash the entered password using sha256
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    while True:
        # Check the hashed password against the value stored in the database
        cur.execute("SELECT * FROM Teacher WHERE Username=? AND Password=?", (username, hashed_password))
        result = cur.fetchone()
        User.username = username
        if result:
            await message.answer(f"Login successful!\n\n")

            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton("Events", callback_data="event_info"),
                types.InlineKeyboardButton("Students", callback_data="students_info")
            )
            keyboard.add(
                types.InlineKeyboardButton("Cabinet", callback_data="cabinet_teacher"),
                types.InlineKeyboardButton("Mentors", callback_data="teachers_info")
            )
            keyboard.add(
                types.InlineKeyboardButton("EXIT", callback_data="stop_teacher")
            )
            await message.answer("Please choose an option:", reply_markup=keyboard)
            await state.finish()
            break
        else:
            await message.answer("Invalid username or password. Please try again.")
            password = await bot.ask(message.chat.id, "Please enter your password:")
            hashed_password = hashlib.sha256(password.encode()).hexdigest()




@dp.callback_query_handler(lambda c: c.data == "login_student")
async def login_callback(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer("Please enter your student number:")
    await state.set_state("login_student_number")

@dp.message_handler(state="login_student_number")
async def login_student_number_cmd(message: types.Message, state: FSMContext):
    student_number = message.text
    await state.update_data(student_number=student_number)
    User.studentNumber = student_number
    await message.answer("Please enter your password:")
    await state.set_state("login_password_student")
class ContactState(StatesGroup):
    expecting_contact = State()

@dp.callback_query_handler(lambda c: c.data == 'add_contact')
async def process_callback_add_contact(callback_query: types.CallbackQuery, state: FSMContext):
    # Prompt the user to input their contact information
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Please enter your contact information.")

    # Update the user's state to expect the contact information
    await ContactState.expecting_contact.set()
    await state.update_data(user_id=callback_query.from_user.id)


@dp.message_handler(state=ContactState.expecting_contact)
async def process_contact_message(message: types.Message, state: FSMContext):
    # Get the user ID from the state
    data = await state.get_data()
    user_id = data.get("user_id")

    # Get the contact information from the message
    contact = message.text

    # Insert the contact into the database
    cur.execute("UPDATE Student SET Contact = ? WHERE StudentNumber = ?", (contact, User.studentNumber))
    db.commit()

    await bot.send_message(chat_id=message.chat.id, text=f"Contact added successfully: {contact}")

    # Reset the state
    await state.reset_state()

@dp.callback_query_handler(lambda c: c.data == 'cabinet')
async def process_callback_edit_student_data(callback_query: types.CallbackQuery, state: FSMContext):
    # Get the student number from the state
    data = await state.get_data()
    student_number = User.studentNumber
    # Query the database for the student's information
    cur.execute("SELECT FirstName, LastName, name FROM Student JOIN Specialization ON Student.id_spec = Specialization.id_spec WHERE StudentNumber = ?", (student_number,))
    student = cur.fetchone()
    # Check if any data was returned
    if student:
        # Format the student information as a string
        FirstName, LastName, spec_name = student
        student_text = f"Full name: {FirstName} {LastName}\nSpecialization: {spec_name}\n\n"
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Edit first name", callback_data="edit_first_name"))
        keyboard.add(InlineKeyboardButton("Edit last name", callback_data="edit_last_name"))
        keyboard.add(InlineKeyboardButton("Edit specialization", callback_data="edit_specialization"))
        keyboard.add(InlineKeyboardButton("Add telegram contact", callback_data="add_contact"))
        await bot.send_message(chat_id=callback_query.message.chat.id, text=student_text, reply_markup=keyboard)
    else:
        # Send a message indicating that no data was found
        await bot.send_message(chat_id=callback_query.message.chat.id, text=f"No data found for the logged student. SN: {User.studentNumber}")



@dp.callback_query_handler(lambda c: c.data == 'edit_first_name')
async def process_callback_edit_first_name(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state("first_new_name")
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Please enter the new first name:")

@dp.message_handler(lambda message: message.text, state="first_new_name")
async def process_first_name(message: types.Message, state: FSMContext):
    new_first_name = message.text
    data = await state.get_data()
    student_number = User.studentNumber
    cur.execute("UPDATE Student SET FirstName = ? WHERE StudentNumber = ?", (new_first_name, student_number))
    db.commit()
    await bot.send_message(chat_id=message.chat.id, text=f"First name updated to {new_first_name}")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'edit_last_name')
async def process_callback_edit_last_name(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state("last_new_name")
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Please enter the new last name:")

@dp.message_handler(lambda message: message.text, state="last_new_name")
async def process_last_name(message: types.Message, state: FSMContext):
    new_last_name = message.text
    data = await state.get_data()
    student_number = User.studentNumber
    cur.execute("UPDATE Student SET LastName = ? WHERE StudentNumber = ?", (new_last_name, student_number))
    db.commit()
    await bot.send_message(chat_id=message.chat.id, text=f"Last name updated to {new_last_name}")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'edit_specialization')
async def process_callback_edit_specialization(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state("new_specialization")
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Please enter the new specialization id:\n1-Backend\n2-Frontend\n3-Data Science\n4-Project Manager\n5-QA")

@dp.message_handler(lambda message: message.text, state="new_specialization")
async def process_specialization(message: types.Message, state: FSMContext):
    new_specialization_id = int(message.text)
    data = await state.get_data()
    student_number = User.studentNumber
    cur.execute("UPDATE Student SET id_spec = ? WHERE StudentNumber = ?", (new_specialization_id, student_number))
    db.commit()
    await bot.send_message(chat_id=message.chat.id, text=f"Specialization updated to {new_specialization_id}")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'faq')
async def process_callback_faq(callback_query: types.CallbackQuery):
    # Query the database for all questions and answers from the FAQ table
    cur.execute("SELECT question, answer FROM FAQ")
    faq = cur.fetchall()

    # Check if any data was returned
    if faq:
        # Format the FAQ as a string
        faq_text = "Frequently Asked Questions:\n\n"
        for question, answer in faq:
            faq_text += f"Q: {question}\nA: {answer}\n\n"
        # Send the FAQ to the chat
        await bot.send_message(chat_id=callback_query.message.chat.id, text=faq_text)
    else:
        # Send a message indicating that no data was found
        await bot.send_message(chat_id=callback_query.message.chat.id, text="No data found in the FAQ table.")


MAX_CALLBACK_DATA_LENGTH = 64

@dp.callback_query_handler(lambda c: c.data.startswith('all_event'))
async def process_callback_event(callback_query: types.CallbackQuery):
    global message_ids
    # Extract the current page number from the callback data
    current_page = int(callback_query.data.split(':')[1]) if ':' in callback_query.data else 0
    # Calculate the offset for the SQL query
    offset = current_page * 5
    # Query the database for 5 events from the Source table
    cur.execute("SELECT id_source, company FROM Source LIMIT 5 OFFSET ?", (offset,))
    source = cur.fetchall()

    # Check if any data was returned
    if source:
        # Delete the previous page's messages
        for message_id in message_ids:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=message_id)
        # Clear the message IDs list
        message_ids = []
        # Create an inline keyboard with a button for each event
        keyboard = InlineKeyboardMarkup()
        for id_source, company in source:
            # Truncate the company value if necessary
            company = company[:MAX_CALLBACK_DATA_LENGTH - len("event:")]
            keyboard.add(InlineKeyboardButton(company, callback_data=f"event:{id_source}"))
        # Add navigation buttons to the keyboard
        if current_page > 0:
            keyboard.add(InlineKeyboardButton("Previous", callback_data=f"all_event:{current_page - 1}"))
        if len(source) == 5:
            keyboard.add(InlineKeyboardButton("Next", callback_data=f"all_event:{current_page + 1}"))
        # Send the keyboard to the chat
        message = await bot.send_message(chat_id=callback_query.message.chat.id, text="All events:", reply_markup=keyboard)
        # Store the message ID
        message_ids.append(message.message_id)
    else:
        # Send a message indicating that no data was found
        await bot.send_message(chat_id=callback_query.message.chat.id, text="No events found in the Source table.")
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('event:'))
async def process_callback_event_info(callback_query: types.CallbackQuery):
    # Get the id of the selected event from the callback data
    id_source = callback_query.data.split(':')[1]
    # Query the database for the event information
    cur.execute("SELECT link, description, data FROM Source WHERE id_source = ?", (id_source,))
    event = cur.fetchone()
    # Check if any data was returned
    if event:
        # Format the event information as a string
        link, description, data = event
        event_text = f"Link: {link}\n\nDescription: {description}\n\nData: {data}\n\n"
        # Send the event information to the chat
        await bot.send_message(chat_id=callback_query.message.chat.id, text=event_text)
    else:
        # Send a message indicating that no data was found
        await bot.send_message(chat_id=callback_query.message.chat.id, text="No event found with the selected id.")

# Create a variable to track whether the user is logged in or not
user_logged_in = False
# Create a variable to track whether the bot is active or not
bot_active = True


@dp.callback_query_handler(lambda c: c.data == 'recommend_event')
async def recommend_event(callback_query: types.CallbackQuery):
    # Get the id of the student who triggered the callback query
    student_id = callback_query.from_user.id

    # Query the database to find the student's specialization
    cur.execute("SELECT id_spec FROM Student WHERE StudentNumber = ?", (User.studentNumber,))
    specialization_id = cur.fetchone()[0]

    # Query the database to find all sources associated with the student's specialization
    cur.execute(
        "SELECT id_source, link, description, data, company FROM Source INNER JOIN source_special_tkl ON Source.id_source = source_special_tkl.id_source_spec WHERE source_special_tkl.id_spec_source = ?",
        (specialization_id,))
    source = cur.fetchall()

    # Check if any data was returned
    if source:
        # Create a list to hold the messages sent to the chat
        messages = []
        # Create an inline keyboard with a button for each source
        keyboard = InlineKeyboardMarkup()
        for id_source, link, description, data, company in source:
            # Truncate the description value if necessary
            description = description[:MAX_CALLBACK_DATA_LENGTH - len("source:")]
            keyboard.add(InlineKeyboardButton(description, callback_data=f"source:{id_source}"))
            # Create a string with the source information
            source_text = f"Link: {link}\n\nDescription: {description}\n\nData: {data}\n\nCompany: {company}\n\n"
            # Add the source information to the list of messages
            messages.append(source_text)
        # Send the keyboard to the chat
        message = await bot.send_message(chat_id=callback_query.message.chat.id, text="Sources:", reply_markup=keyboard)
        # Store the message ID
        messages.append(message.message_id)
        # Store the messages in the global dictionary using the chat ID as the key
        message_dict[chat_id] = messages
    else:
        # Send a message indicating that no data was found
        await bot.send_message(chat_id=callback_query.message.chat.id, text="No sources found for your specialization.")




@dp.callback_query_handler(lambda c: c.data == 'stop_student')
async def process_callback_stop(callback_query: types.CallbackQuery):
    global bot_active
    # Stop the bot
    bot_active = False
    User.studentNumber=""

    # Clear the conversation
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)




@dp.callback_query_handler(lambda c: c.data == 'stop_teacher')
async def process_callback_stop(callback_query: types.CallbackQuery):
    global bot_active
    # Stop the bot
    bot_active = False
    User.username=""

    # Clear the conversation
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)



@dp.callback_query_handler(lambda c: c.data == 'cabinet_teacher')
async def process_callback_cabinet_teacher(callback_query: types.CallbackQuery, state: FSMContext):
    # Get the username from the state
    data = await state.get_data()
    username = User.username
    # Query the database for the teacher's information
    cur.execute("SELECT FirstName, LastName, Description, ContactData FROM Teacher WHERE Username = ?", (username,))
    teacher = cur.fetchone()
    # Check if any data was returned
    keyboard = InlineKeyboardMarkup(row_width=1)
    if teacher:
        # Format the teacher information as a string
        FirstName, LastName, Description, ContactData = teacher
        teacher_text = f"Full name: {FirstName} {LastName}\nDescription: {Description}\nContact Data: {ContactData}\n\n"
        keyboard.add(InlineKeyboardButton("Edit data", callback_data="edit_data_cabinet"))
        keyboard.add(InlineKeyboardButton("Delete data", callback_data="delete_data_cabinet"))
        # Send the teacher information to the chat
        await bot.send_message(chat_id=callback_query.message.chat.id, text=teacher_text, reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'delete_data_cabinet')
async def process_callback_delete_data_cabinet(callback_query: types.CallbackQuery, state: FSMContext):
    # Get the username from the state
    data = await state.get_data()
    username = User.username
    # Query the database to delete the teacher's information
    cur.execute("DELETE FROM Teacher WHERE Username = ?", (username,))
    # Commit the changes to the database
    db.commit()
    User.username =""
    # Send a confirmation message to the chat
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Teacher data deleted.")

@dp.callback_query_handler(lambda c: c.data == 'edit_data_cabinet')
async def process_callback_edit_data_cabinet(callback_query: types.CallbackQuery, state: FSMContext):
    # Get the username from the state
    data = await state.get_data()
    username = User.username
    # Query the database for the teacher's information
    cur.execute("SELECT FirstName, LastName, Description, ContactData FROM Teacher WHERE Username = ?", (username,))
    teacher = cur.fetchone()
    # Check if any data was returned
    if teacher:
        # Format the teacher information as a string
        FirstName, LastName, Description, ContactData = teacher
        teacher_text = f"Full name: {FirstName} {LastName}\nDescription: {Description}\nContact Data: {ContactData}\n\n"
        # Create an inline keyboard with buttons for each field
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("Edit First Name", callback_data="edit_first_name_teacher"))
        keyboard.add(InlineKeyboardButton("Edit Last Name", callback_data="edit_last_name_teacher"))
        keyboard.add(InlineKeyboardButton("Edit Description", callback_data="edit_description_teacher"))
        keyboard.add(InlineKeyboardButton("Edit Contact Data", callback_data="edit_contact_teacher"))
        # Send the teacher information and inline keyboard to the chat
        await bot.send_message(chat_id=callback_query.message.chat.id, text=teacher_text, reply_markup=keyboard)




@dp.callback_query_handler(lambda c: c.data == 'edit_contact_teacher')
async def process_callback_edit_contact_name_teacher(callback_query: types.CallbackQuery, state: FSMContext):
    # Get the username from the state
    data = await state.get_data()
    username = User.username
    # Send a message to the user asking for their new first name
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Please enter your new description:")
    # Set the state to expect a new first name
    await state.set_state("edit_contact_teacher")


@dp.message_handler(state="edit_contact_teacher")
async def process_message_edit_contact_name_teacher(message: types.Message, state: FSMContext):
    # Get the username from the state
    data = await state.get_data()
    username = User.username
    # Get the new first name from the message
    new_contact = message.text
    # Update the first name in the database
    cur.execute("UPDATE Teacher SET ContactData = ? WHERE Username = ?", (new_contact, username))
    # Reset the state
    db.commit()
    await bot.send_message(chat_id=message.chat.id, text="Your contact has been updated successfully!")
    await state.reset_state()



@dp.callback_query_handler(lambda c: c.data == 'edit_description_teacher')
async def process_callback_edit_desc_name_teacher(callback_query: types.CallbackQuery, state: FSMContext):
    # Get the username from the state
    data = await state.get_data()
    username = User.username
    # Send a message to the user asking for their new first name
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Please enter your new description:")
    # Set the state to expect a new first name
    await state.set_state("edit_description_teacher")


@dp.message_handler(state="edit_description_teacher")
async def process_message_edit_desc_name_teacher(message: types.Message, state: FSMContext):
    # Get the username from the state
    data = await state.get_data()
    username = User.username
    # Get the new first name from the message
    new_desc = message.text
    # Update the first name in the database
    cur.execute("UPDATE Teacher SET Description = ? WHERE Username = ?", (new_desc, username))
    # Reset the state
    db.commit()
    await bot.send_message(chat_id=message.chat.id, text="Your description has been updated successfully!")
    await state.reset_state()


@dp.callback_query_handler(lambda c: c.data == 'edit_first_name_teacher')
async def process_callback_edit_first_name_teacher(callback_query: types.CallbackQuery, state: FSMContext):
    # Get the username from the state
    data = await state.get_data()
    username = User.username
    # Send a message to the user asking for their new first name
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Please enter your new first name:")
    # Set the state to expect a new first name
    await state.set_state("edit_first_name_teacher")


@dp.message_handler(state="edit_first_name_teacher")
async def process_message_edit_first_name_teacher(message: types.Message, state: FSMContext):
    # Get the username from the state
    data = await state.get_data()
    username = User.username
    # Get the new first name from the message
    new_first_name = message.text
    # Update the first name in the database
    cur.execute("UPDATE Teacher SET FirstName = ? WHERE Username = ?", (new_first_name, username))
    # Reset the state
    db.commit()
    await bot.send_message(chat_id=message.chat.id, text="Your first name has been updated successfully!")
    await state.reset_state()


@dp.callback_query_handler(lambda c: c.data == 'edit_last_name_teacher')
async def process_callback_edit_last_name_teacher(callback_query: types.CallbackQuery, state: FSMContext):
    # Get the username from the state
    data = await state.get_data()
    username = User.username
    # Send a message to the user asking for their new first name
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Please enter your new last name:")
    # Set the state to expect a new first name
    await state.set_state("edit_last_name_teacher")


@dp.message_handler(state="edit_last_name_teacher")
async def process_message_edit_last_name_teacher(message: types.Message, state: FSMContext):
    # Get the username from the state
    data = await state.get_data()
    username = User.username
    # Get the new first name from the message
    new_last_name = message.text
    # Update the first name in the database
    cur.execute("UPDATE Teacher SET LastName = ? WHERE Username = ?", (new_last_name, username))
    # Reset the state
    db.commit()
    await bot.send_message(chat_id=message.chat.id, text="Your last name has been updated successfully!")
    await state.reset_state()




MAX_CALLBACK_DATA_LENGTH_info = 64

@dp.callback_query_handler(lambda c: c.data.startswith('event_info'))
async def process_callback_event_info(callback_query: types.CallbackQuery):
    global message_ids
    # Extract the current page number from the callback data
    current_page = int(callback_query.data.split(':')[1]) if ':' in callback_query.data else 0
    # Calculate the offset for the SQL query
    offset = current_page * 5
    # Query the database for 5 events from the Source table
    cur.execute("SELECT id_source, company FROM Source LIMIT 5 OFFSET ?", (offset,))
    source = cur.fetchall()
    keyboard = InlineKeyboardMarkup()
    # Check if any data was returned
    if source:

        # Delete the previous page's messages
        for message_id in message_ids:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=message_id)
        # Clear the message IDs list
        message_ids = []
        # Create an inline keyboard with a button for each event
        keyboard = InlineKeyboardMarkup()
        for id_source, company in source:
            # Truncate the company value if necessary
            company = company[:MAX_CALLBACK_DATA_LENGTH_info - len("event:")]
            keyboard.add(InlineKeyboardButton(company, callback_data=f"event_:{id_source}"))
        # Add navigation buttons to the keyboard
        if current_page > 0:
            keyboard.add(InlineKeyboardButton("Previous", callback_data=f"event_info:{current_page - 1}"))
        if len(source) == 5:
            keyboard.add(InlineKeyboardButton("Next", callback_data=f"event_info:{current_page + 1}"))
        keyboard.add(InlineKeyboardButton("Create new event", callback_data="create_new_event"))
        # Send the keyboard to the chat
        message = await bot.send_message(chat_id=callback_query.message.chat.id, text="All events:", reply_markup=keyboard)
        # Store the message ID
        message_ids.append(message.message_id)
    else:
        keyboard.add(InlineKeyboardButton("Create new event", callback_data="create_new_event"))
        # Send a message indicating that no data was found
        await bot.send_message(chat_id=callback_query.message.chat.id, text="No events found in the Source table.", reply_markup=keyboard)



@dp.callback_query_handler(lambda c: c.data and c.data.startswith('event_:'))
async def process_callback_event_info_(callback_query: types.CallbackQuery):
    # Get the id of the selected event from the callback data
    id_source = callback_query.data.split(':')[1]
    # Query the database for the event information
    cur.execute("SELECT link, description, data FROM Source WHERE id_source = ?", (id_source,))
    event = cur.fetchone()
    # Check if any data was returned
    keyboard = InlineKeyboardMarkup()
    if event:
        # Format the event information as a string
        link, description, data = event
        event_text = f"Link: {link}\n\nDescription: {description}\n\nData: {data}\n\n"
        # Send the event information to the chat

        keyboard.add(InlineKeyboardButton("Edit event", callback_data=f"edit_event:{id_source}"))
        keyboard.add(InlineKeyboardButton("Delete event", callback_data=f"delete_event:{id_source}"))
        await bot.send_message(chat_id=callback_query.message.chat.id, text=event_text, reply_markup=keyboard)
    else:
        # Send a message indicating that no data was found
        await bot.send_message(chat_id=callback_query.message.chat.id, text="No event found with the selected id.")


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('edit_event'))
async def edit_event(callback_query: types.CallbackQuery):
    # Get the id of the selected event from the callback data
    id_source = callback_query.data.split(':')[1]
    # Query the database for the event information
    cur.execute("SELECT link, description, data, company FROM Source WHERE id_source = ?", (id_source,))
    event = cur.fetchone()
    # Check if any data was returned
    if event:
        # Format the event information as a string
        link, description, data, company = event
        event_text = f"Link: {link}\n\nDescription: {description}\n\nData: {data}\n\nCompany: {company}\n\n"
        # Create an inline keyboard with buttons to edit each field
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Edit link", callback_data=f"edit_link:{id_source}"))
        keyboard.add(InlineKeyboardButton("Edit description", callback_data=f"edit_description:{id_source}"))
        keyboard.add(InlineKeyboardButton("Edit data", callback_data=f"edit_data:{id_source}"))
        keyboard.add(InlineKeyboardButton("Edit company", callback_data=f"edit_company:{id_source}"))
        # Send the event information and inline keyboard to the chat
        await bot.send_message(chat_id=callback_query.message.chat.id, text=event_text, reply_markup=keyboard)
    else:
        # Send a message indicating that no data was found
        await bot.send_message(chat_id=callback_query.message.chat.id, text="No event found with the selected id.")

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('delete_event'))
async def delete_event(callback_query: types.CallbackQuery):
    # Get the id of the selected event from the callback data
    id_source = callback_query.data.split(':')[1]
    # Delete the event from the database
    cur.execute("DELETE FROM Source WHERE id_source = ?", (id_source,))
    db.commit()
    # Send a confirmation message to the chat
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Event deleted successfully!")
class FormEvent(StatesGroup):
    edit_link = State()
    edit_description = State()
    edit_date = State()
    edit_company = State()
    # Add additional states for other fields here



class FormNewEvent(StatesGroup):
    elink = State()
    description = State()
    date = State()
    company = State()
    num_specializations = State()
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('create_new_event'))
async def create_new_event(callback_query: types.CallbackQuery):
    # Set the state to "elink" and store the chat_id in the state data
    await FormNewEvent.elink.set()
    await dp.current_state(chat=callback_query.message.chat.id).update_data(
        chat_id=callback_query.message.chat.id)
    # Send a message asking the user to enter the link for the new event
    await bot.send_message(chat_id=callback_query.message.chat.id,
                           text="Please enter the link for the new event:")


@dp.message_handler(state=FormNewEvent.elink)
async def process_new_event_link(message: types.Message, state: FSMContext):
    # Store the link in the state data
    await state.update_data(link=message.text)
    # Set the state to "description"
    await FormNewEvent.description.set()
    # Send a message asking the user to enter the description for the new event
    await bot.send_message(chat_id=message.chat.id, text="Please enter the description for the new event:")

@dp.message_handler(state=FormNewEvent.description)
async def process_new_event_description(message: types.Message, state: FSMContext):
    # Store the description in the state data
    await state.update_data(description=message.text)
    # Set the state to "date"
    await FormNewEvent.date.set()
    # Send a message asking the user to enter the date for the new event
    await bot.send_message(chat_id=message.chat.id, text="Please enter the date for the new event:")

    @dp.message_handler(state=FormNewEvent.date)
    async def process_new_event_date(message: types.Message, state: FSMContext):
        # Store the date in the state data
        await state.update_data(date=message.text)
        # Set the state to "company"
        await FormNewEvent.num_specializations.set()
        # Send a message asking the user to enter the company for the new event
        await bot.send_message(chat_id=message.chat.id, text="Please choose spec for event:\n1-Backend\n2-Frontend\n3-Data Science\n4-Project Manager\n5-QA ")


@dp.message_handler(state=FormNewEvent.num_specializations)
async def process_new_event_spec(message: types.Message, state: FSMContext):
    # Store the number of specializations in the state data
    await state.update_data(num_specializations=message.text)
    # Set the state to "date"
    await FormNewEvent.company.set()
    # Send a message asking the user to enter the date for the new event
    await bot.send_message(chat_id=message.chat.id, text="Please enter the company for the new event:")


@dp.message_handler(state=FormNewEvent.company)
async def process_new_event_company(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    link = state_data['link']
    description = state_data['description']
    date = state_data['date']
    company = message.text

    # Insert a new row into the Source table with all of this data
    cur.execute("INSERT INTO Source (link, description, data, company) VALUES (?, ?, ?, ?)",
                (link, description, date, company))
    db.commit()

    # Get the ID of the newly inserted row
    source_id = cur.lastrowid

    # Get the specializations selected by the user
    specializations = state_data['num_specializations']

    # Insert a new row into the source_special_tkl table for each specialization
    for spec_id in specializations:
        cur.execute("INSERT INTO source_special_tkl (id_source_spec, id_spec_source) VALUES (?, ?)",
                    (source_id, spec_id))
        db.commit()

    # Reset the state
    await state.finish()

    # Send a confirmation message to the chat
    await bot.send_message(chat_id=message.chat.id, text="Event created successfully!")


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('edit_link'))
async def edit_link(callback_query: types.CallbackQuery):
    # Get the id of the selected event from the callback data
    id_source = callback_query.data.split(':')[1]
    # Set the state to "edit_link" and store the id_source in the state data
    await FormEvent.edit_link.set()
    await dp.current_state(chat=callback_query.message.chat.id).update_data(id_source=id_source)
    # Send a message asking the user to enter a new link
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Please enter a new link:")

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('edit_description'))
async def edit_description(callback_query: types.CallbackQuery):
    # Get the id of the selected event from the callback data
    id_source = callback_query.data.split(':')[1]
    # Set the state to "edit_description" and store the id_source in the state data
    await FormEvent.edit_description.set()
    await dp.current_state(chat=callback_query.message.chat.id).update_data(id_source=id_source)
    # Send a message asking the user to enter a new description
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Please enter a new description:")

@dp.message_handler(state=FormEvent.edit_description)
async def process_new_description(message: types.Message, state: FSMContext):
    # Get the id_source from the state data
    state_data = await state.get_data()
    id_source = state_data['id_source']
    # Update the description in the database
    cur.execute("UPDATE Source SET description = ? WHERE id_source = ?", (message.text, id_source))
    db.commit()
    # Reset the state
    await state.finish()
    # Send a confirmation message to the chat
    await bot.send_message(chat_id=message.chat.id, text="Description updated successfully!")
@dp.message_handler(state=FormEvent.edit_link)
async def process_new_link(message: types.Message, state: FSMContext):
    # Get the id_source from the state data
    state_data = await state.get_data()
    id_source = state_data['id_source']
    # Update the link in the database
    cur.execute("UPDATE Source SET link = ? WHERE id_source = ?", (message.text, id_source))
    db.commit()
    # Reset the state
    await state.finish()
    # Send a confirmation message to the chat
    await bot.send_message(chat_id=message.chat.id, text="Link updated successfully!")


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('edit_data'))
async def edit_date(callback_query: types.CallbackQuery):
    # Get the id of the selected event from the callback data
    id_source = callback_query.data.split(':')[1]
    # Set the state to "edit_description" and store the id_source in the state data
    await FormEvent.edit_date.set()
    await dp.current_state(chat=callback_query.message.chat.id).update_data(id_source=id_source)
    # Send a message asking the user to enter a new description
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Please enter a new date:")


@dp.message_handler(state=FormEvent.edit_date)
async def process_new_date(message: types.Message, state: FSMContext):
    # Get the id_source from the state data
    state_data = await state.get_data()
    id_source = state_data['id_source']
    # Update the description in the database
    cur.execute("UPDATE Source SET data = ? WHERE id_source = ?", (message.text, id_source))
    db.commit()
    # Reset the state
    await state.finish()
    # Send a confirmation message to the chat
    await bot.send_message(chat_id=message.chat.id, text="Date updated successfully!")

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('edit_company'))
async def edit_date(callback_query: types.CallbackQuery):
    # Get the id of the selected event from the callback data
    id_source = callback_query.data.split(':')[1]
    # Set the state to "edit_description" and store the id_source in the state data
    await FormEvent.edit_company.set()
    await dp.current_state(chat=callback_query.message.chat.id).update_data(id_source=id_source)
    # Send a message asking the user to enter a new description
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Please enter a new company:")


@dp.message_handler(state=FormEvent.edit_company)
async def process_new_company(message: types.Message, state: FSMContext):
    # Get the id_source from the state data
    state_data = await state.get_data()
    id_source = state_data['id_source']
    # Update the description in the database
    cur.execute("UPDATE Source SET company = ? WHERE id_source = ?", (message.text, id_source))
    db.commit()
    # Reset the state
    await state.finish()
    # Send a confirmation message to the chat
    await bot.send_message(chat_id=message.chat.id, text="Company updated successfully!")

@dp.callback_query_handler(lambda c: c.data == "delete_result")
async def process_callback_delete_result(callback_query: CallbackQuery):
    cur.execute('UPDATE Student SET points=0 WHERE StudentNumber=?', (User.studentNumber,))
    db.commit()
    await bot.answer_callback_query(callback_query.id, text="Your quiz result has been deleted.")
@dp.callback_query_handler(lambda c: c.data.startswith('quiz:'))
async def process_callback_quiz(callback_query: CallbackQuery):
    try:
        # Check if user already has points in the database
        cur.execute('SELECT points FROM Student WHERE StudentNumber=?', (User.studentNumber,))
        current_points = cur.fetchone()

        if current_points is not None and current_points[0] > 0:
            await bot.send_message(callback_query.from_user.id, text="You have already taken the quiz and have points. If you want to retake the quiz, please delete your previous result.")
            inline_keyboard = InlineKeyboardMarkup(row_width=1)
            inline_keyboard.add(InlineKeyboardButton(text="Delete Result", callback_data="delete_result"))
            await bot.send_message(callback_query.from_user.id,
                                   text="Would you like to delete your previous quiz result?",
                                   reply_markup=inline_keyboard)
            return

        # Get the question id from the callback data
        question_id = int(callback_query.data.split(':')[1])
    except (ValueError, IndexError):
        logging.warning(f"Invalid quiz callback data: {callback_query.data}")
        return

    # Get the question and answers from the database
    cur.execute('SELECT question FROM questions WHERE id=?', (question_id,))
    question = cur.fetchone()[0]

    cur.execute('SELECT answer, points FROM answers WHERE question_id=?', (question_id,))
    answers = cur.fetchall()

    # Create the message with the question and answers
    message = f'{question}\n\n'
    for i, answer in enumerate(answers):
        message += f'{chr(ord("a") + i)}) {answer[0]}\n\n'

    # Create the inline keyboard with the answer options
    inline_keyboard = InlineKeyboardMarkup(row_width=4)
    for i, answer in enumerate(answers):
        inline_keyboard.insert(InlineKeyboardButton(text=chr(ord("a") + i), callback_data=f'answer:{answer[1]}'))

    # Add the "Next" button
    inline_keyboard.add(InlineKeyboardButton(text="Next", callback_data=f"next:{question_id}"))

    # Send the message with the inline keyboard
    await bot.send_message(callback_query.from_user.id, text=message, reply_markup=inline_keyboard)


# Define the callback query handler for the answers
# Define the callback query handler for the answers
@dp.callback_query_handler(lambda c: c.data.startswith('answer:'))
async def process_callback_answer(callback_query: CallbackQuery):
    try:
        # Get the answer points from the callback data
        answer_points = int(callback_query.data.split(':')[1])

        # Get the student's current points and specialization from the database
        cur.execute('SELECT points, id_spec FROM Student WHERE StudentNumber=?', (User.studentNumber,))
        current_points, current_spec_id = cur.fetchone()

        # Get the specialization points from the database
        cur.execute('SELECT id_spec, points FROM Specialization')
        spec_points = cur.fetchall()

        # Calculate the difference between the student's current points and each specialization's points
        diff = {}
        for spec in spec_points:
            diff[spec[0]] = abs(current_points + answer_points - spec[1])

        # Find the specialization with the smallest difference and set it as the student's specialization
        new_spec_id = min(diff, key=diff.get)
        cur.execute('UPDATE Student SET points=?, id_spec=? WHERE StudentNumber=?',
                    (current_points + answer_points, new_spec_id, User.studentNumber))
        db.commit()

        # Answer the callback query with the points added message
        await bot.answer_callback_query(callback_query.id, text=f'You got {answer_points} point(s)!')

    except (ValueError, IndexError, TypeError):
        logging.warning(f"Invalid answer callback data: {callback_query.data}")


# Define the callback query handler for the "Next" button
@dp.callback_query_handler(lambda c: c.data.startswith('next:'))
async def process_callback_next(callback_query: CallbackQuery):
    try:
        # Get the question id from the callback data
        question_id = int(callback_query.data.split(':')[1])

        # Get the next question id from the database
        cur.execute('SELECT id FROM questions WHERE id > ? ORDER BY id LIMIT 1', (question_id,))
        next_question_id = cur.fetchone()

        if next_question_id:
            inline_keyboard = InlineKeyboardMarkup(row_width=3)
            inline_keyboard.add(InlineKeyboardButton(text="Next", callback_data=f"next:{next_question_id[0]}"))

            # Get the question and answers for the next question
            cur.execute('SELECT question FROM questions WHERE id=?', (next_question_id[0],))
            question = cur.fetchone()[0]
            cur.execute('SELECT answer, points FROM answers WHERE question_id=?', (next_question_id[0],))
            answers = cur.fetchall()
            # Create the message with the question and answers
            message = f'{question}\n\n'
            for i, answer in enumerate(answers):
                message += f'{chr(ord("a") + i)}) {answer[0]}\n'

            # Create the inline keyboard with the answer options
            inline_keyboard = InlineKeyboardMarkup(row_width=4)
            for i, answer in enumerate(answers):
                inline_keyboard.insert(
                    InlineKeyboardButton(text=chr(ord("a") + i), callback_data=f'answer:{answer[1]}'))

            # Add the "Next" button
            inline_keyboard.add(InlineKeyboardButton(text="Next", callback_data=f"next:{next_question_id[0]}"))

            # Send the message with the inline keyboard
            await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                        message_id=callback_query.message.message_id,
                                        text=message, reply_markup=inline_keyboard)

        else:
            # No more questions, end the quiz
            await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                        message_id=callback_query.message.message_id,
                                        text="Congratulations, you have finished the quiz!")

    except (ValueError, IndexError):
        logging.warning(f"Invalid next callback data: {callback_query.data}")


@dp.message_handler(state="password")
async def password_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    student_number = data.get("student_number")
    password = message.text
    password_is_valid = False

    # Keep asking for a password until it is valid
    while not password_is_valid:
        # Validate the password
        if len(password) < 4:
            await message.answer("Invalid password. Password must be at least 4 characters long.")
        elif not re.search(r"[a-z]", password) or not re.search(r"[A-Z]", password):
            await message.answer("Invalid password. Password must contain both uppercase and lowercase Latin characters.")
        else:
            password_is_valid = True

        if not password_is_valid:
            # Ask for a new password
            await state.set_state("password_retry")
            return

    # Hash the password before storing it
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    await state.update_data(password=hashed_password)

    await message.answer("Please enter your first name:")
    await state.set_state("first_name")


@dp.message_handler(state="password_retry")
async def password_retry_cmd(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    await password_cmd(message, state)

@dp.callback_query_handler(lambda c: c.data == 'btn_event')
async def show_event_options(callback_query: types.CallbackQuery):
    all_event_keyboard = InlineKeyboardMarkup(row_width=1)
    all_event_keyboard.add(InlineKeyboardButton(text="All Events", callback_data="all_event"))

    recommend_event_keyboard = InlineKeyboardMarkup(row_width=1)
    recommend_event_keyboard.add(InlineKeyboardButton(text="My Recommended Events", callback_data="recommend_event"))

    await bot.send_message(callback_query.from_user.id,
                           text="Which events would you like to see?",
                           reply_markup=all_event_keyboard)
    await bot.send_message(callback_query.from_user.id,
                           text="Or would you like to see your recommended events?",
                           reply_markup=recommend_event_keyboard)



@dp.message_handler(commands=['menu'])
async def menu_command(message: types.Message, state: FSMContext):
    data = await state.get_data()
    username = User.username
    student_number = User.studentNumber

    cur.execute("SELECT 1 FROM Teacher WHERE Username = ?", (username,))
    is_teacher = cur.fetchone() is not None
    # Check if the user is a logged-in student
    cur.execute("SELECT 1 FROM Student WHERE StudentNumber = ?", (student_number,))
    is_student = cur.fetchone() is not None
    if is_teacher:
        # Show the teacher menu
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("Events", callback_data="event_info"),
            types.InlineKeyboardButton("Students", callback_data="students_info")
        )
        keyboard.add(
            types.InlineKeyboardButton("Cabinet", callback_data="cabinet_teacher"),
            types.InlineKeyboardButton("Mentors", callback_data="teachers_info")
        )
        keyboard.add(
            types.InlineKeyboardButton("EXIT", callback_data="stop_teacher")
        )
        await message.answer("Teacher Menu", reply_markup=keyboard)
    elif is_student:
        # Show the student menu
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("Events", callback_data="btn_event"),
            types.InlineKeyboardButton("Quiz", callback_data="quiz:1")
        )
        keyboard.add(
            types.InlineKeyboardButton("Mentors", callback_data="teachers_info"),
            types.InlineKeyboardButton("Cabinet", callback_data="cabinet")
        )
        keyboard.add(
            types.InlineKeyboardButton("Contact Creator", url="https://t.me/vl_los"),
            types.InlineKeyboardButton("FAQ", callback_data="faq")
        )
        keyboard.add(
            types.InlineKeyboardButton("EXIT", callback_data="stop_student")
        )
        await message.answer("Student Menu", reply_markup=keyboard)
    else:
        await message.answer(f"You must be logged in as a student or teacher to access the menu.{username}")



@dp.callback_query_handler()
async def process_callback(callback_query: types.CallbackQuery):
    global bot_active
    # Check if the bot is active
    if not bot_active:
        # If the bot is not active, send a message indicating that it is inactive
        await callback_query.answer("The bot is currently inactive. Please log in and send the /start command to reactivate it.")


@dp.message_handler(state="login_password_student")
async def login_password_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    student_number = data.get("student_number")

    # Ask the user to enter their password until it's correct
    while True:
        entered_password = message.text

        # Hash the entered password
        hashed_entered_password = hashlib.sha256(entered_password.encode()).hexdigest()

        # Retrieve the stored hashed password from the database
        cur.execute(
            "SELECT * FROM Student WHERE StudentNumber=?",
            (student_number,)
        )
        user_data = cur.fetchone()

        if user_data:
            stored_hashed_password = user_data[4]

            # Compare the two hashed passwords
            if hashed_entered_password == stored_hashed_password:
                await state.update_data(student_number=student_number)
                response = f"Login successful!\n\n"
                await message.answer(response)

                keyboard = types.InlineKeyboardMarkup(row_width=2)
                keyboard.add(
                    types.InlineKeyboardButton("Events", callback_data="btn_event"),
                    types.InlineKeyboardButton("Quiz", callback_data="quiz:1")
                )
                keyboard.add(
                    types.InlineKeyboardButton("Mentors", callback_data="teachers_info"),
                    types.InlineKeyboardButton("Cabinet", callback_data="cabinet")
                )
                keyboard.add(
                    types.InlineKeyboardButton("Contact Creator", url="https://t.me/vl_los"),
                    types.InlineKeyboardButton("FAQ", callback_data="faq")
                )
                keyboard.add(
                    types.InlineKeyboardButton("EXIT", callback_data="stop_student")
                )

                await message.answer("Please choose an option:", reply_markup=keyboard)

                break  # exit the loop since the password is correct
            else:
                await message.answer("Invalid student number or password. Please try again.")
        else:
            await message.answer("Invalid student number or password. Please try again.")

        # Wait for the next message from the same chat as the original message
        async for new_message in dp.current_state(chat=message.chat.id):
            if new_message.text:
                message = new_message
                break

    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)