# Terminal-chat functions file.

import mysql.connector
import termios
import select
import time
import sys
import tty
import os

def get_key(timeout=None) -> str:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(sys.stdin.fileno())

        if timeout:
            ready, _, _ = select.select([sys.stdin], [], [], timeout)
            if sys.stdin in ready:
                char = sys.stdin.read(1)
            else:
                char = None
        else:
            char = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return char

def connect_to_db(host, user, password):
    try:
        mydb = mysql.connector.connect(
            host = host,
            user = user,
            password = password
        )

        mydb.autocommit = True
        return mydb

    except:
        print("Can't connect to database.")
        sys.exit(0)

class App:

    def __init__(self, cursor):
        self.cursor = cursor
        self.in_chat = False
        self.break_loop = False
        self.scrolled_up = 0
    
    # PRETTIER FUNCTIONS

    def text_box(self, text) -> str:
        self.height, self.width = os.popen('stty size', 'r').read().split()
        w = int(self.width) - 4
        m_l = round((w - 2 - len(text)) / 2)
        m_r = w - 2 - m_l - len(text)
        return f'\n  ╭{((w-2)*"─")}╮\n  │{(m_l*" ")}{text}{(m_r*" ")}│  \n  ╰{((w-2)*"─")}╯  \n'
    
    def format_chat_list(self, chat) -> str:
        return f'{chat[1]} | Created by {(self.find_name_by_id(chat[2]))}'

    def format_message(self, message) -> str:
        return f"   {message[2]} │ {self.find_name_by_id(message[0])}: {message[1]}"
    
    # APP SECTION

    def start_app(self):
        self.user_id = (-1)
        self.logged_in = False

        try:
            with open("user.id", "r") as file:
                content = file.read()
        
            if len(content) > 0:
                content = content.split("\n")
                self.remember_me = True if content[0] == "1" else False
                self.user_id = int(content[1])
                self.logged_in = True
                self.set_user_online()
        except:
            self.remember_me = False

    def menu(self):
        os.system("clear")
        print(self.text_box(f"Terminal chat."))
        if (self.remember_me or self.user_id != (-1)):
            options = ["Chats list", "Sign out", "Unregister", "Exit"] 
        else:
            options = ["Log in", "Register", "About","Exit"]
        
        for index, item in enumerate(options):
            print(f'   {index + 1}. {item}\n',end='')

    def app(self):
        while True:
            if self.break_loop:
                os.system("clear")
                break

            if not self.in_chat:
                self.menu()
                option = get_key()

                match option:
                    case "1":
                        self.chats_list() if self.remember_me or self.logged_in else self.log_in()
                    case "2":
                        self.sign_out() if self.remember_me or self.logged_in else self.registration()
                    case "3":
                        self.unregistration() if self.remember_me or self.logged_in else self.about()
                    case "4":
                        self.exit_app()
            else:
                self.print_chat()
                key = get_key(timeout=0.5)
                if str(key) != "None" and type(key) == str:
                    match key.lower():
                        case "t":
                            self.input_message()
                        case "q":
                            self.chats_list()
                        case "w":
                            if self.scrolled_up < self.messages_amount - int(self.height) + 11:
                                self.scrolled_up += 1
                        case "s":
                            if self.scrolled_up > 0:
                                self.scrolled_up -= 1
                        case "a":
                            self.add_user_to_chat(self.chat_choosen)
                
    # SQL QUERIES SECTION

    def chat_users_online(self):
        query = f"""
            SELECT cu.user_id
            FROM chats_users cu
            JOIN users u ON cu.user_id = u.user_id
            WHERE cu.chat_id = {self.chat_choosen} AND u.is_online = 1
        """
        self.cursor.execute(query)
        ids_online = [x for x in self.cursor.fetchall()]
        users_online = ""
        for user_id in ids_online:   
            if int(user_id[0]) == int(self.user_id):         
                users_online += f"\033[1m{self.find_name_by_id(user_id[0])}\033[0m, "
            else:
                users_online += f"{self.find_name_by_id(user_id[0])}, "

        return users_online[:-2]

    def set_user_online(self):
        self.cursor.execute(f"UPDATE users SET is_online = 1 WHERE user_id = {self.user_id};")
    
    def set_user_offline(self):
        self.cursor.execute(f"UPDATE users SET is_online = 0 WHERE user_id = {self.user_id};")

    def find_my_id(self) -> int:
        if self.user_id == -1:
            self.cursor.execute(f"SELECT user_id FROM users WHERE username = '{self.username}';")
            result = self.cursor.fetchone()

            if result:
                return int(result[0])
        else:
            return int(self.user_id)
        
        return -1
        
    def find_name_by_id(self, user_id) -> str:
        self.cursor.fetchall()
        self.cursor.execute(f"SELECT username FROM users WHERE user_id = {user_id};")
        result = self.cursor.fetchone()

        if result:
            return str(result[0])
        
        return ""

    def find_id_by_name(self, username) -> int:
        self.cursor.execute(f"SELECT user_id FROM users WHERE username = '{username}';")
        result = self.cursor.fetchone()

        if result:
            return int(result[0])
        
        return -2

    def register_user(self, username, password):
        self.cursor.execute(f"INSERT INTO `chat`.`users` (`username`, `password`, `is_online`, `unregistered`) VALUES ('{username}', '{password}', 0, 0);")

    def unregister_user(self):
        self.cursor.execute(f"UPDATE users SET unregistered = 1 WHERE user_id = {self.user_id};")
        
    def insert_new_chat(self, chat_name, user_id):
        self.cursor.execute(f"INSERT INTO `chat`.`chats` (`chat_name`, `created_by`) VALUES ('{chat_name}', '{user_id}');")

    def insert_user_to_chat(self, chat_id, user_id):
        self.cursor.execute(f"INSERT INTO `chat`.`chats_users` (`chat_id`, `user_id`) VALUES ('{chat_id}', '{user_id}');")
    
    def find_my_chats_ids(self) -> int:
        self.cursor.execute(f"SELECT chat_id FROM chats_users WHERE user_id = '{self.user_id}';")
        chats_ids = [int(x[0]) for x in self.cursor.fetchall()]
        return chats_ids

    def find_chats(self) -> list:
        chats = []
        for chat_id in self.find_my_chats_ids():
            self.cursor.execute(f"SELECT * FROM chats WHERE chat_id = {chat_id};")
            chats.append([str(x) for x in self.cursor.fetchone()])

        return chats

    def find_chat_name_by_id(self, chat_id) -> str:
        self.cursor.execute(f"SELECT chat_name FROM chats WHERE chat_id = {chat_id};")
        return (self.cursor.fetchone())[0]

    def created_properly(self, chat_name):
        chat_created = False
        self.cursor.fetchall()
        self.cursor.execute(f"SELECT * FROM chats WHERE created_by = {self.user_id};")
        for x in self.cursor:
            chat_created = True
            real_chat_id, real_chat_name, real_created_by = int(x[0]), str(x[1]), int(x[2])

        if (not chat_created) or (chat_name != real_chat_name or self.user_id != real_created_by):
            return False, int(-1)

        return True, real_chat_id

    def insert_message_to_chat(self, message):
        self.cursor.execute(f"INSERT INTO messages (chat_id, sender_id, content, timestamp) VALUES ({self.chat_choosen}, {self.user_id}, '{message}', NOW());")

    def list_messages(self) -> list:
        self.cursor.execute(f"SELECT MAX(message_id) FROM messages WHERE chat_id = {self.chat_choosen};")
        self.messages_amount = self.cursor.fetchone()[0]
        if str(self.messages_amount) == "None":
            self.cursor.execute(f"SELECT * FROM messages WHERE chat_id = {self.chat_choosen};")
        elif 0 <= int(self.messages_amount) <= (int(self.messages_amount) - int(self.height) + 11 - self.scrolled_up):
            self.cursor.execute(f"SELECT * FROM messages WHERE chat_id = {self.chat_choosen};")
        else:
            msg_from = int(self.messages_amount) - int(self.height) + 11 - self.scrolled_up
            msg_to = int(self.messages_amount) - self.scrolled_up
            self.cursor.execute(f"SELECT * FROM messages WHERE chat_id = {self.chat_choosen} AND message_id BETWEEN {msg_from} AND {msg_to};")
        return [[int(x[2]), str(x[3]), str(x[4])] for x in self.cursor.fetchall()]

    # MENU OPTIONS

    def about(self):
        os.system("clear")
        print(self.text_box(f'About.'))
        try:
            with open("about.txt", 'r') as f:
                lines = f.readlines()
                print(*lines)
            get_key()
        except:
            pass

    def log_in(self):
        os.system("clear")
        print(self.text_box("Log in"))
        self.username = input("   Input username: ")
        password = input("   Input password: ")
        print("   Remember me? (y/n): ")
        remember_me = get_key()

        self.cursor.execute(f"SELECT * FROM users WHERE username = '{self.username}'")
        result = self.cursor.fetchone()

        if result:
            real_username, real_password, unregistered = result[1], result[2], result[4]

            if unregistered != 1:
                if password == real_password:
                    self.user_id = self.find_my_id()
                    self.remember_me = True if remember_me.lower() == "y" else False

                    if self.remember_me:
                        with open("user.id", "w") as file:
                            file.write(f"1\n{self.user_id}")

                    self.set_user_online()
                    self.logged_in = True
                    print("\n   Succesfully logged in!")
                else:
                    print("\n   Wrong password!")
            else:
                print("\n   User unregistered.")
        else:
            print("\n   This username doesn't exist!")

        time.sleep(0.8)

    def sign_out(self, auto='n'):
            key = 'n'
            if auto == 'n':
                os.system("clear")
                print(self.text_box("Sign out."))
                print(f"   Are you sure you want to sign out? (y/n):")
                key = get_key()

            if (str(key)).lower() == "y" or auto == 'y':
                self.user_id = (-1)
                self.logged_in = False
                self.remember_me = False
                self.set_user_offline()

                try:
                    with open("user.id", "r") as f:
                        os.remove("user.id")
                except:
                    pass

    def registration(self):
        os.system("clear")
        print(self.text_box("Registration"))
        username = input("   Input username: ")
        password = input("   Input password: ")
        already_exists = False

        try:
            self.cursor.execute(f"SELECT * FROM users WHERE username = '{username}';")
            result = self.cursor.fetchone()

            if result:
                already_exists = True

            if not already_exists:
                self.register_user(username, password)
                print('\n   Account registered successfully!\n   Now you can log in.')
            else:
                print('\n   Username is already taken!')
        except:
            print('\n   Sorry, something went wrong.')
        
        time.sleep(0.8)

    def unregistration(self):
        os.system("clear")
        unregistered = False
        print(self.text_box("Unregistration."))
        print(f"   Are you sure you want to unregister?")
        print(f"   You won't be able to use the account again! (y/n):")
        key = str(get_key())
        try:
            if key.lower() == "y":
                self.unregister_user()
                self.set_user_offline()
                print(f"\n   Unregistered successfuly!")
                unregistered = True
                time.sleep(0.8)
                self.sign_out('y')
            elif key.lower() != "y":
                print(f"\n   Stopping unregistration.")
        except:
            print("\n   Sorry, something went wrong!")
        if not unregistered:
            time.sleep(0.8)

    def chats_list(self):
        os.system("clear")
        print(self.text_box(f"Your chats."))
        self.in_chat = False
        not_number = False
        chats = self.find_chats()
        print(f"   1. Create a new chat.\n")
        for index, chat in enumerate(chats):
            print(f'   {index + 2}. {self.format_chat_list(chat)}')
        
        option = get_key()

        try:
            int(option)
        except:
            not_number = True
            if option == "q":
                self.menu()
            else:
                self.chats_list()

        if option == "1":
            self.create_new_chat()
        elif not not_number:
            if 1 < int(option) <= len(chats) + 1:
                self.chat_choosen = (chats[int(option) - 2][0])
                self.in_chat = True
        else:
            print('Wrong option chosen.')
            
    def print_chat(self):
        os.system("clear")
        print(self.text_box(f"{self.find_chat_name_by_id(self.chat_choosen)}"))
        print(f"   Users Online: {self.chat_users_online()}\n")
        for message in self.list_messages():
            print(self.format_message(message))

    def input_message(self):
            message = str(input("\nType: "))
            if len(message) > 0:
                try:
                    self.insert_message_to_chat(message)
                except:
                    print("Something went wrong.")
                    time.sleep(0.8)

    def add_user_to_chat(self, chat_id):
        username = str(input("Input username to add: "))
        self.cursor.fetchall()
        user_id = self.find_id_by_name(username)
        if user_id == (-2):
            print("User doesn't exist.")
        else:
            try:
                self.insert_user_to_chat(chat_id, user_id)
                print("User added succesfully.")
            # except mysql.connector.custom_error_exception(): #duplicated key primary
                # print("User is already member of this chat.")
            except:
                print("Something went wrong.")

        time.sleep(0.8)

    def create_new_chat(self):
        os.system("clear")
        print(f'{self.text_box("New chat")}')
        chat_name = str(input("   Input chat name: "))
        username = str(input("   Input recipient username: "))
        recipient_id = self.find_id_by_name(username)
        if recipient_id != (-2) and recipient_id != (-1):
            self.insert_new_chat(chat_name, self.user_id)
            created, real_chat_id = self.created_properly(chat_name)
        
            if created:
                try:
                    self.insert_user_to_chat(real_chat_id, self.user_id)
                    self.insert_user_to_chat(real_chat_id, recipient_id)
                    print(f'\n   Succesfully created chat!')
                except:
                    print(f"\n   Ups, something went wrong. :(")
            else:
                print(f"\n   Ups, something went wrong. :(")
        else:
            print(f"\n   Can't find user '{username}'.\n   Chat not created.")

        time.sleep(0.8)
        self.chats_list()

    def exit_app(self):
        self.break_loop = True
        self.set_user_offline()
        os.system("clear")