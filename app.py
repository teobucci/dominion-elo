import json

import altair as alt
import pandas as pd
import numpy as np

import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime

# funzioni personalizzate
from round_robin import get_rr_rounds
from functions_elo import new_elos, get_K, aggiornaVinteDisputate, aggiornaElo, get_vinte_disputate
from functions_gdrive import write_df_in_spreadsheet, get_worksheet
from functions_streamlit import plotEloDataframe

# COSTANTI
with open('json/settings.json') as f:
    data = json.load(f)

# questo lo importo perché fa comodo
# ["Teo", "Jacopo", "Randa", "Marco", "Tommaso", "Braga"]
players_names = data['players_names']


st.markdown("# DOMINION")

st.write("Link utili ai fogli:")
st.markdown("[Foglio Calcoli](" + str(data['link_sheet_calcolo_elo']) + ")", unsafe_allow_html=True)
st.markdown("[Foglio Punteggi](" + str(data['link_sheet_punteggi']) + ")", unsafe_allow_html=True)


class Player:
    player_id = 0

    def __init__(self, elo, name, presence):
        self.elo = elo
        self.name = name
        self.presence = presence

        # per l'aggiornamento di vinte disputate
        self.vinte = 0
        self.disputate = 0

        # ID
        Player.player_id += 1


# inizializzo i giocatori, con ELO 1500 e presenti
players = [Player(1500, player_name, True) for player_name in players_names]
# print(players[0].__dict__)

st.markdown("## Estrazione torneo")

# creo il dizionario delle presente, formato da giocatore: true/false, dove le values
# le ottengo con una comprehension di checkbox al variare dei giocatori
presence = dict(zip(players_names,
                    [st.checkbox(player, True)
                     for player in players_names] * len(players_names)
                    ))

# seleziono i giocatori giocanti (presenti)
playing = [player_name for player_name, present in presence.items() if present == True]

if(st.button("Estrai!")):
    # estraggo i turni
    turni = get_rr_rounds(playing)

    st.write("Ecco i turni estratti")
    # 3 colonne, la terza 4 volte più grande delle prime due
    cols = st.beta_columns([1, 1, 4])
    for index, turno in enumerate(turni):
        cols[0].markdown(f'**Turno**')
        cols[1].markdown(f'**{index+1}**')

        for partita in turno:
            # salto le partite vuote
            if partita[0] == 'DUMMY' or partita[1] == 'DUMMY':
                continue
            cols[0].write(f'{partita[0]}')
            cols[1].write(f'{partita[1]}')

    text_turni = ""
    for index, turno in enumerate(turni):
        for partita in turno:
            # salto le partite vuote
            if partita[0] == 'DUMMY' or partita[1] == 'DUMMY':
                continue
            text_turni += partita[0]
            text_turni += "\n"
            text_turni += partita[1]
            text_turni += "\n"
    # rimuovo l'ultimo accapo
    text_turni = text_turni[:-1]
    cols[2].text_area(
        "Ecco invece per il copia-incolla sullo Sheet:", text_turni, height=text_turni.count('\n')*27)

st.markdown("---")
st.markdown("## Punteggi ELO")


col1, col2 = st.beta_columns((1, 1))
startDate = col1.date_input("INIZIO", datetime(2021, 1, 1))
endDate = col2.date_input("FINE", datetime.today())
st.markdown("⚠️ Il sistema delle date è WIP")
# TODO


st.markdown("---")

st.markdown("Il seguente pulsante guarda il foglio dei punteggi e aggiorna, sovrascrivendo ogni volta per intero, il foglio _Vinte e Disputate_, usato poi nel calcolo dell'Elo.")


if(st.button("1. Aggiorna \"Vinte e Disputate\"")):

    sheets_dict = pd.read_excel(data['sheet_punteggi_xls'], sheet_name=None)

    vinte_disputate = aggiornaVinteDisputate(sheets_dict, players)

    # lo devo scrivere su google

    # rendo l'indice una colonna e lo converto in stringa (sarebbe una data)
    new_df = vinte_disputate.copy()
    new_df.sort_values('data', ascending=True, inplace=True)
    new_df.reset_index(inplace=True)
    new_df['data'] = new_df['data'].dt.strftime('%d/%m/%Y')

    write_df_in_spreadsheet(data['vinte_disputate_worksheet_name'], data['id_sheet_elo'], data['credentials_json_path'], new_df)

st.markdown("Questo pulsante legge il foglio _Vinte e Disputate_ e aggiorna il foglio dei punteggi ELO.")

if(st.button("2. Aggiorna il foglio")):  # TODO

    # carico il df
    vinte_disputate_df = pd.read_csv(data['vinte_disputate_csv'], decimal=',')

    vinte, disputate = get_vinte_disputate(vinte_disputate_df, players)

    # ora che ho il dataframe lo dò in pasto alla funzione aggiornaElo,
    # insieme alla lista di players
    elo_df = aggiornaElo(players, vinte, disputate, data['K_ref_6_players'])

    # scrivo

    elo_df.reset_index(inplace=True)

    # converto in stringa in modo da poterlo scrivere
    elo_df['data'] = elo_df['data'].dt.strftime('%d/%m/%Y')

    my_worksheet = get_worksheet(data['elo_worksheet_name'], data['id_sheet_elo'], data['credentials_json_path'])

    # value_input_option='USER_ENTERED' serve per evitare che le date diventino '20/10/2020 con il tick
    # https://stackoverflow.com/questions/62358444/how-to-format-a-datetime-so-google-sheets-recognise-the-value-as-date-time
    my_worksheet.update('A6', elo_df.values.tolist(), value_input_option='USER_ENTERED')


st.markdown("Questo pulsante legge il foglio dei punteggi ELO e sputa fuori tutte le statistiche.")

if st.button("3. Leggi dal foglio (+ stats)"):

    elos_worksheet = get_worksheet(data['elo_worksheet_name'], data['id_sheet_elo'], data['credentials_json_path'])
    #elo_df_retrieved = pd.DataFrame(elos_worksheet.get_all_records())

    # value_render_option serve per avere i numeri con la virgola
    df_dates = pd.DataFrame(elos_worksheet.get('A6:A100'))
    df_elos = pd.DataFrame(elos_worksheet.get('B6:G100', value_render_option='UNFORMATTED_VALUE'))

    elo_df = pd.concat([df_dates, df_elos], axis=1)

    elo_df.columns = ['data'] + players_names

    elo_df['data'] = pd.to_datetime(elo_df['data'], format="%d/%m/%Y")

    elo_df.set_index('data', inplace=True)

    # prendo le vinte e disputate che servono per il winrate
    vinte_disputate_df = pd.read_csv(data['vinte_disputate_csv'], decimal=',')
    vinte, disputate = get_vinte_disputate(vinte_disputate_df, players)

    plotEloDataframe(elo_df, vinte, disputate)


st.markdown("---")


if st.button("All-inclusive: aggiorna Vinte e Disputate, calcola Elo, leggi Elo"):

    # AGGIORNA

    sheets_dict = pd.read_excel(data['sheet_punteggi_xls'], sheet_name=None)
    vinte_disputate = aggiornaVinteDisputate(sheets_dict, players)

    # rendo l'indice una colonna e lo converto in stringa (sarebbe una data)
    new_df = vinte_disputate.copy()
    new_df.sort_values('data', ascending=True, inplace=True)
    new_df.reset_index(inplace=True)
    new_df['data'] = new_df['data'].dt.strftime('%d/%m/%Y')

    write_df_in_spreadsheet(data['vinte_disputate_worksheet_name'], data['id_sheet_elo'], data['credentials_json_path'], new_df)

    # CALCOLA

    vinte_disputate.sort_values('data', ascending=True, inplace=True)
    vinte_disputate.reset_index(inplace=True)

    vinte, disputate = get_vinte_disputate(vinte_disputate, players)

    elo_df = aggiornaElo(players, vinte, disputate, data['K_ref_6_players'])

    # converto la data in stringa in modo da poterlo scrivere
    elo_df.reset_index(inplace=True)
    elo_df['data'] = elo_df['data'].dt.strftime('%d/%m/%Y')

    my_worksheet = get_worksheet(data['elo_worksheet_name'], data['id_sheet_elo'], data['credentials_json_path'])

    # value_input_option='USER_ENTERED' serve per evitare che le date diventino '20/10/2020 con il tick
    # https://stackoverflow.com/questions/62358444/how-to-format-a-datetime-so-google-sheets-recognise-the-value-as-date-time
    my_worksheet.update('A6', elo_df.values.tolist(), value_input_option='USER_ENTERED')

    # LEGGI

    elo_df['data'] = pd.to_datetime(elo_df['data'], format="%d/%m/%Y")

    elo_df.set_index('data', inplace=True)

    plotEloDataframe(elo_df, vinte, disputate)


if(st.button("Mostra i Campioni (richiede molta potenza)")):
    # devo recuperare due nuove tabelle con le vittorie secondo la logica di Dominion

    sheets_dict = pd.read_excel(data['sheet_punteggi_xls'], sheet_name=None)
    vinte_disputate_dom = aggiornaVinteDisputate(sheets_dict, players, roundUP=True)

    # spacco in due il dataframe
    vinte_dom = vinte_disputate_dom.iloc[:, 0::2]
    vinte_dom.columns = players_names
    disputate_dom = vinte_disputate_dom.iloc[:, 1::2]
    disputate_dom.columns = players_names

    # questa tabella è T/F se è in corrispondenza di un campione
    tabella_verita = disputate_dom[(vinte_dom == disputate_dom) & (disputate_dom != 0)]

    # semplifico droppando i NaN
    tabella_verita.dropna(how='all', inplace=True)

    # i possibili valori
    ns = [3, 4, 5]

    def buildName(n):
        return f'Campioni {n}/{n}'

    # creo un dizionario di dataframe
    champions_collection = dict()
    for n in ns:
        champions_collection[buildName(n)] = pd.DataFrame(
            columns=['Giocatore'])

    # non so minimamente cosa faccia stack(), ma così mi restituisce le coppie indice/colonna da esaminare
    label_da_esaminare = list(tabella_verita.stack().index)

    for label in label_da_esaminare:
        date = label[0]
        name = label[1]
        nn = disputate_dom.loc[date, name]  # i punti di questa

        # aggiorno il dataframe "nn"=1,2,3, in corrispondenza della data nella colonna "Giocatore"
        # con il nome del giocatore campione
        champions_collection[buildName(nn)].loc[date, 'Giocatore'] = name

    # li mostro
    for key in champions_collection.keys():
        st.markdown(str(key))
        st.write(champions_collection[key])


# TODO
# date importanti (espansioni) nel grafico

# https://docs.gspread.org/en/latest/user-guide.html#using-gspread-with-pandas
