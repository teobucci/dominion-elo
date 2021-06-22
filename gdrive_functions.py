import gspread


def write_df_in_spreadsheet(worksheet_name, sheet_id, credentials_json_path, my_dataframe):
    """
    I:
    sheet_id: id dell'intero sheet
    worksheet_name: nome dello specifico foglio di lavoro da sovrascrivere
    credentials_json_path: path del file json con le credenziali
    my_dataframe: contenuto da scrivere
    """

    # ACCESS GOOGLE SHEET
    drive_client = gspread.service_account(filename=credentials_json_path)
    sh = drive_client.open_by_key(sheet_id)
    worksheet = sh.worksheet(worksheet_name)

    # APPEND DATA TO SHEET
    worksheet.update([my_dataframe.columns.values.tolist()] +
                     my_dataframe.values.tolist())
