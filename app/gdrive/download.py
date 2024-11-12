import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Путь к вашему файлу с данными сервисного аккаунта
SERVICE_ACCOUNT_FILE = '/code/app/gdrive/service-account-file.json'

# Получение аутентификационных данных и создание клиента для Google Drive API
def create_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=credentials)
    return service

# Функция для получения ID файла по имени и создания прямой ссылки на скачивание
def get_file_id_and_download_link(folder_name, file_name):
    service = create_drive_service()
    
    # Добавляем расширение .txt к имени файла
    file_name = file_name + ".txt"

    # Поиск папки 'Alpha' в корневом каталоге
    alpha_query = "name='Alpha' and mimeType='application/vnd.google-apps.folder'"
    alpha_results = service.files().list(q=alpha_query).execute()
    alpha_folders = alpha_results.get('files', [])

    if not alpha_folders:
        return f"Ошибка!(not alpha_folders)"

    alpha_id = alpha_folders[0]['id']

    # Поиск указанной папки внутри папки 'Alpha'
    folder_query = f"'{alpha_id}' in parents and name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    folder_results = service.files().list(q=folder_query).execute()
    folders = folder_results.get('files', [])

    if not folders:
        return f"Ошибка!(not folders)"

    folder_id = folders[0]['id']

    # Поиск файла по имени в указанной папке
    file_query = f"'{folder_id}' in parents and name='{file_name}'"
    file_results = service.files().list(q=file_query).execute()
    files = file_results.get('files', [])

    if not files:
        return f"Ошибка!(not files)"

    file_id = files[0]['id']
    download_link = f"https://drive.google.com/uc?export=download&id={file_id}"

    return download_link
