import json

import altair as alt
import pandas as pd
import numpy as np

import streamlit as st
import matplotlib.pyplot as plt

# funzioni personalizzate
from round_robin import get_rr_rounds
from elo_functions import new_elos, get_K
from gdrive_functions import write_df_in_spreadsheet


# COSTANTI

with open('json/settings.json') as f:
    data = json.load(f)

# questo lo importo perché fa comodo
# ["Teo", "Jacopo", "Randa", "Marco", "Tommaso", "Braga"]
players_names = data['players_names']


st.markdown("# DOMINION")

st.write("Link utili ai fogli:")
st.markdown("[Foglio Calcoli](" +
            str(data['link_sheet_calcolo_elo']) + ")", unsafe_allow_html=True)
st.markdown("[Foglio Punteggi](" +
            str(data['link_sheet_punteggi']) + ")", unsafe_allow_html=True)


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
playing = [player_name for player_name,
           present in presence.items() if present == True]


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

    # st.write("Ecco invece per il copia-incolla sullo Sheet:")
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
st.markdown(
    "Il seguente pulsante analizza il foglio _Vinte e Disputate_ e ne calcola gli Elo.")


def aggiornaElo(players, vinte_disputate_df):
    """
    I: players (lista di oggetti Player), vinte_disputate_df dataframe
    O: dataframe di elo
    Dipende da new_elos
    """

    elo_list = []
    start_row = [player.elo for player in players]
    # TODO sistemare l'inizio data
    start_row.insert(0, pd.to_datetime('2020-12-31'))
    elo_list.append(start_row)

    number_of_total_players = int(vinte_disputate_df.shape[1]/2)

    for indice_riga in range(vinte_disputate_df.shape[0]):

        # controllo chi era presente
        for idx, player in enumerate(players):
            # se le disputate sono zero
            if (int(vinte_disputate_df.iloc[indice_riga, 2*idx+1]) == 0):
                player.presence = False
            else:
                player.presence = True

        # genero una lista dei giocatori presenti
        playing = []
        playing = [player for player in players if player.presence == True]

        # genero una lista degli elo dei presenti
        playing_elos = [player.elo for player in playing]

        # trovo i punteggi effettivi
        effective_scores = []
        for idx, player in enumerate(players):
            if player.presence == True:
                # appendo il punteggio effettivo (2*i perché non considero le disputate)
                effective_scores.append(
                    float(vinte_disputate_df.iloc[indice_riga, 2*idx]))

        # determino il k da usare
        number_of_playing = len(playing)
        my_k = get_K(number_of_playing, number_of_total_players,
                     data['K_ref_6_players'])

        # genero una lista dei nuovi elo (sempre solo dei presenti)
        my_new_elos = new_elos(effective_scores, playing_elos, my_k)

        # aggiorno gli elo dei giocatori (tutti stavolta, in realtà
        # chi non c'era non lo cambio, ma ciclo su tutti)
        for player in players:
            if player.presence == True:
                # gli metto il primo disponibile e lo brucio con pop
                player.elo = my_new_elos.pop(0)

        # genero la nuova riga aggiungere, devo includere la data
        # prima metto tutti gli elo nuovi
        nuova_partita = [player.elo for player in players]
        # poi aggiungo la data in posizione 0, la quale è l'indice del df
        nuova_partita.insert(0, vinte_disputate_df.index[indice_riga])

        # finalmente aggiungo la lista
        elo_list.append(nuova_partita)

    # creo l'header
    header = [player.name for player in players]
    header.insert(0, 'data')

    # creo il dataframe a partire dalla lista di liste
    elo_df = pd.DataFrame(elo_list, columns=header)

    # imposto l'indice
    elo_df.set_index('data', inplace=True)

    # lo mostro
    # elo_df.head()
    return elo_df


def pandaSeries_to_md_table(serie):
    righe = ["|", "|", "|"]
    for idx, value in serie.items():  # idx è il giocatore
        righe[0] += idx + '|'
        righe[1] += ':---:' + '|'
        righe[2] += str(round(value)) + '|'

    return righe[0] + '\n' + righe[1] + '\n' + righe[2]


if(st.button("Calcola ELO")):

    status_calcola_elo = st.empty()

    # carico il df
    status_calcola_elo.text("Carico il dataframe...")
    vinte_disputate_df = pd.read_csv(data['vinte_disputate_csv'], decimal=',')

    # converto la colonna data nel formato data
    vinte_disputate_df['data'] = pd.to_datetime(
        vinte_disputate_df['data'], format='%d/%m/%Y')
    # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior

    # la imposto come indice
    vinte_disputate_df.set_index('data', inplace=True)

    # ora che ho il dataframe lo dò in pasto alla funzione aggiornaElo,
    # insieme alla lista di players
    status_calcola_elo.text("Genero i nuovi elo...")
    elo_df = aggiornaElo(players, vinte_disputate_df)

    status_calcola_elo.text("Completato. Ecco i plot:")

    # procedo a fare i plot
    source = elo_df.reset_index().melt('data', var_name='player', value_name='elo')
    base = alt.Chart(source).encode(
        x=alt.X('data:T', title='DATA'),
    )
    columns = sorted(source.player.unique())
    selection = alt.selection_single(
        fields=['data'], nearest=True, on='mouseover', empty='none', clear='mouseout'
    )

    lines = base.mark_line().encode(
        # y='elo:Q',
        y=alt.Y('elo:Q', title='ELO', scale=alt.Scale(domain=[1360, 1600])),
        color=alt.Color('player:N', title='GIOCATORE'),
    )
    points = lines.mark_point().transform_filter(selection)

    rule = base.transform_pivot(
        'player', value='elo', groupby=['data']
    ).mark_rule().encode(
        opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
        tooltip=[alt.Tooltip(c, type='quantitative', format='.1f')
                 for c in columns]
    ).add_selection(selection)

    grafico = alt.layer(lines, points, rule).properties(
        width=800,
        height=400
    ).interactive()
    # primo plot
    st.markdown("### Punteggi")
    st.altair_chart(grafico)

    mostra_elo_df = st.beta_expander(
        "Mostra il dataframe degli Elo", expanded=False)
    mostra_elo_df.write(elo_df)

    # elo_df.plot(grid=True)
    #plt.legend(loc='center right', bbox_to_anchor=(1, 0.5))

    st.markdown("### Punteggi normalizzati")
    elo_norm = (elo_df - elo_df.min()) / (elo_df.max()-elo_df.min())
    # elo_norm.plot(kind='kde')
    st.line_chart(elo_norm)

    st.markdown("### Variazioni")
    elo_var = elo_df.diff()
    st.line_chart(elo_var)

    # scelta date
    # da = pd.to_datetime('2021-01-06')
    # a = pd.to_datetime('2021-01-10')
    # st.write(f"Nelle seguenti date ecco i punteggi: da {da} a {a}:")
    # elo_df.loc[da:a]

    statistiche = pd.DataFrame()

    st.markdown("### Classifica")
    classifica = elo_df.iloc[-1]
    # inplace=True fa si che la modifica sia applicata
    classifica.sort_values(ascending=False, inplace=True)
    posto_classifica = 1
    for idx, value in classifica.items():
        st.write(f"{posto_classifica} - {idx}:\t\t{round(value)}")
        posto_classifica += 1

    st.markdown("### Ulteriori statistiche (cioè funzioni dei dati)")

    # st.markdown("### Numero partite vinte e partite disputate")

    # righe = ["||", "|:---|", "|Vinte|", "|Disputate|"]
    # i = 0
    # for idx, value in vinte_disputate_df.sum().items():  # idx è teo_vinte...
    #     if i % 2 == 0:  # è un valore di vinte
    #         righe[0] += players[i//2].name + '|'
    #         righe[2] += str(round(value)) + '|'
    #     else:  # è un valore di disputate
    #         righe[3] += str(round(value)) + '|'
    #     righe[1] += ':---:' + '|'
    #     i += 1
    # tabella_numero_vinte_disputate = righe[0] + '\n' + \
    #     righe[1] + '\n' + righe[2] + '\n' + righe[3]
    # st.markdown(tabella_numero_vinte_disputate)

    statistiche = pd.DataFrame(columns=players_names)

    # media
    statistiche.loc['Media'] = elo_df.mean()

    # vinte e disputate
    # vinte_disputate_df.sum().items() è uno zip, va tradotto in lista per estrarre
    statistiche.loc['Vinte'] = [value for idx, value in list(
        vinte_disputate_df.sum().items())[::2]]
    statistiche.loc['Disputate'] = [value for idx,
                                    value in list(vinte_disputate_df.sum().items())[1::2]]

    # winrate
    statistiche.loc['WinRate complessivo'] = statistiche.loc['Vinte'] / \
        statistiche.loc['Disputate']

    # winrate puntuale
    winrate_df = pd.DataFrame(
        data=None, columns=elo_df.columns, index=vinte_disputate_df.index)
    # per tutte le colonne diviso 2, cioè i giocatori
    for i in range(vinte_disputate_df.shape[1]//2):
        winrate_df.iloc[:, i] = vinte_disputate_df.iloc[:,
                                                        2*i] / vinte_disputate_df.iloc[:, 2*i+1]

    # winrate cumulativo
    vinte_disputate_cumulative_df = vinte_disputate_df.cumsum()
    # ripeto identico
    winrate_cum_df = pd.DataFrame(
        data=None, columns=elo_df.columns, index=vinte_disputate_cumulative_df.index)
    # per tutte le colonne diviso 2, cioè i giocatori
    for i in range(vinte_disputate_cumulative_df.shape[1]//2):
        winrate_cum_df.iloc[:, i] = vinte_disputate_cumulative_df.iloc[:,
                                                                       2*i] / vinte_disputate_cumulative_df.iloc[:, 2*i+1]
    # st.line_chart(winrate_cum_df)

    statistiche.loc['Massimo ELO'] = elo_df.max()
    statistiche.loc['Raggiunto il'] = elo_df.idxmax(axis=0)

    st.write(statistiche)

    mostra_winrate_puntuale = st.beta_expander(
        "Mostra il WinRate puntuale", expanded=False)
    mostra_winrate_puntuale.write(winrate_df)

    mostra_winrate_cum = st.beta_expander(
        "Mostra il WinRate cumulativo", expanded=False)
    mostra_winrate_cum.write(winrate_cum_df)

    st.markdown("WinRate cumulativo")
    st.line_chart(winrate_cum_df.iloc[1:])

    serie_chi_primo_quanto = elo_df.iloc[1:, :].idxmax(
        axis=1).value_counts()  # prendo dal primo gennaio

    st.markdown("Primo per:")
    st.bar_chart(serie_chi_primo_quanto)

st.markdown("---")
st.markdown("## Aggiornamenti")
st.markdown("Il seguente pulsante guarda il foglio dei punteggi e aggiorna, sovrascrivendo ogni volta per intero, il foglio _Vinte e Disputate_, usato poi nel calcolo dell'Elo.")


def aggiornaVinteDisputate(sheets_dict, players):
    """
    I: sheets_dict il dizionario di dataframes, generato dall'excel, players lista di oggetti Player
    O: dataframe vinte_disputate
    """
    head = ['data']
    for name in players_names:
        head.append(name.lower()+'_vinte')
        head.append(name.lower()+'_disputate')

    vinte_disputate = pd.DataFrame(columns=head)
    vinte_disputate.set_index('data', inplace=True)
    # print(head)

    # ciclo sul dizionario, analizzando ogni foglio, che è un dataframe
    for idx, key in enumerate(sheets_dict):

        # key è la data, il nome del foglio
        # sheets_dict[key] è il df

        # prendo solo quelle dopo un certo giorno/anno TODO da sistemare in base alla richiesta
        giorno = pd.to_datetime(key, format='%d%m%Y')
        if giorno.year < 2021:
            continue

        # trovo l'indice in corrispondenza di 'CLASSIFICA'
        index_incriminato = sheets_dict[key][sheets_dict[key]
                                             ['GIOCATORE'] == 'CLASSIFICA'].index[0]

        # elimino tutto ciò che c'è dopo
        sheets_dict[key].drop(
            sheets_dict[key].index[index_incriminato:], inplace=True)

        # elimino due colonne di cui non mi interessa il contenuto
        del sheets_dict[key]['PUNTI']
        del sheets_dict[key]['% PUNTI']

        #giocatori = mydf['GIOCATORE'].unique()

        vinte_disputate_row = []
        for player in players:

            serie_vittorie = sheets_dict[key][sheets_dict[key]
                                              ['GIOCATORE'] == player.name]['VITTORIE']

            player.vinte = sum(serie_vittorie)
            player.disputate = len(serie_vittorie)

            vinte_disputate_row.append(player.vinte)
            vinte_disputate_row.append(player.disputate)

        vinte_disputate.loc[giorno] = vinte_disputate_row

    return vinte_disputate


#progress_bar = st.progress(0)
if(st.button("Aggiorna \"Vinte e Disputate\"")):

    status_text = st.empty()
    status_text.text("Leggo i dati...")
    sheets_dict = pd.read_excel(data['sheet_punteggi_xls'], sheet_name=None)
    # type(sheets_dict) dict
    status_text.text("Analizzo...")
    vinte_disputate = aggiornaVinteDisputate(sheets_dict, players)
    st.write(vinte_disputate)

    # lo devo scrivere su google

    # rendo l'indice una colonna e lo converto in stringa (sarebbe una data)
    new_df = vinte_disputate.copy()
    new_df.sort_values('data', ascending=True, inplace=True)
    new_df.reset_index(inplace=True)
    new_df['data'] = new_df['data'].dt.strftime('%d/%m/%Y')

    status_text.text("Scrivo nel foglio Google...")
    write_df_in_spreadsheet(
        data['vinte_disputate_worksheet_name'], data['id_sheet_elo'], data['credentials_json_path'], new_df)
    status_text.text("Terminato. Ecco i risultati:")


# TODO
# primo per, primo ininterrottamente per
# win rate puntuale e cumulativo + grafici
# campioni 3/3... TOSTO bisogna ripartire dal foglio dei tornei
# date importanti (espansioni)
# mongolini e MVP

# vinte e disputate devono essere due separati
# per consecutivi
# https://stackoverflow.com/questions/26911851/how-to-use-pandas-to-find-consecutive-same-data-in-time-series
