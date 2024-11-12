import shutil
import os
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker
from cli.subscription import get_config, ConfigFormat

# Глобальные переменные
DATABASE_URL = 'sqlite:////var/lib/marzban/db.sqlite3?check_same_thread=False'
COPY_DATABASE_PATH = './copy_db.sqlite3'
COPY_DATABASE_URL = f'sqlite:///{COPY_DATABASE_PATH}'
SERVER_NAME = 'Alpha'  # Название сервера

def copy_database():
    # Копирование базы данных
    shutil.copy('/var/lib/marzban/db.sqlite3', COPY_DATABASE_PATH)

def process_users():
    try:
        # Копируем базу данных
        copy_database()

        # Создание подключения к копии базы данных с помощью SQLAlchemy
        engine = create_engine(COPY_DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Чтение данных из таблицы users и admins с помощью SQLAlchemy
        metadata = MetaData()
        users_table = Table('users', metadata, autoload_with=engine)
        admins_table = Table('admins', metadata, autoload_with=engine)

        # Запрос к базам данных, чтобы получить username и соответствующее admin_name
        stmt = select([users_table.c.username, admins_table.c.username.label('admin_name')]).select_from(
            users_table.join(admins_table, users_table.c.admin_id == admins_table.c.id))
        result = session.execute(stmt).fetchall()

        if not result:
            print("No users found in the database.")
            return

        # Словарь соответствия username и admin_name
        user_admin_map = {item['username']: item['admin_name'] for item in result}

        print(f"User-Admin map: {user_admin_map}")

        # Закрытие сессии, чтобы избежать ошибок потоков
        session.close()

        # Цикл обработки каждого пользователя вне сессии
        for username, admin_name in user_admin_map.items():
            output_file = f"/var/lib/marzban/gdrive_mount/{SERVER_NAME}/{admin_name}/{username}.txt"
            config_format = ConfigFormat.v2ray  # or ConfigFormat.clash depending on your requirement
            as_base64 = True  # Set to True if you want the output in base64 format

            # Вызов функции get_config
            try:
                print(f"Processing config for user: {username} under admin: {admin_name}")
                get_config(username=username, config_format=config_format, output_file=output_file, as_base64=as_base64)
                print(f"Processed config for user: {username} under admin: {admin_name}")
            except Exception as e:
                print(f"NOT ERROR!")
                # Подробный вывод исключения
                import traceback
                traceback.print_exc()

        # Удаление копии базы данных
        os.remove(COPY_DATABASE_PATH)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Удаление копии базы данных в случае ошибки
        if os.path.exists(COPY_DATABASE_PATH):
            os.remove(COPY_DATABASE_PATH)
        # Подробный вывод исключения
        import traceback
        traceback.print_exc()
