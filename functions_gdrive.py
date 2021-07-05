import gspread
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
import streamlit as st


# VERSIONE ORIGINALE
# def get_worksheet(worksheet_name, sheet_id, credentials_json_path):
#     """
#     I:
#     worksheet_name: nome dello sheet come stringa
#     sheet_id: id dello sheet, preso dall'url, come stringa
#     credentials_json_path: path dove sta il file json di credenziali, come stringa, relativo
#     O:
#     un oggetto worksheet della libreria gspread
#     """
#     drive_client = gspread.service_account(filename=credentials_json_path)
#     sh = drive_client.open_by_key(sheet_id)
#     worksheet = sh.worksheet(worksheet_name)
#     return worksheet

# VERSIONE PER FUNZIONARE CON STREAMLIT.SECRETS
# la libreria oauth2 serve solo in questo caso per poter dare i valori tramite st.secrets e non
# dal json
def get_worksheet(worksheet_name, sheet_id, credentials_json_path):

    DEFAULT_SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
    ]

    credentials = ServiceAccountCredentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=DEFAULT_SCOPES,
    )

    drive_client = gspread.authorize(credentials)

    #drive_client = gspread.service_account(filename=credentials_json_path)
    sh = drive_client.open_by_key(sheet_id)
    worksheet = sh.worksheet(worksheet_name)
    return worksheet


def write_df_in_spreadsheet(worksheet_name, sheet_id, credentials_json_path, my_dataframe):
    """
    I:
    sheet_id: id dell'intero sheet
    worksheet_name: nome dello specifico foglio di lavoro da sovrascrivere
    credentials_json_path: path del file json con le credenziali
    my_dataframe: contenuto da scrivere
    """

    worksheet = get_worksheet(worksheet_name, sheet_id, credentials_json_path)

    # APPEND DATA TO SHEET
    worksheet.update([my_dataframe.columns.values.tolist()] + my_dataframe.values.tolist())
