import pandas as pd
import numpy as np


def expected_1_v_others(player_elo, other_elos):
    """
    I: un punteggio e una lista di altri punteggi
    O: expected di quel giocatore
    """
    # solita formula elo per calcolare expected
    return sum([1/(1+10**((other_elo - player_elo)/400)) for other_elo in other_elos])


def get_all_expected(elos):
    """
    I: lista di elo
    O: lista di expected
    Si appoggia a expected_1_v_others
    """
    expected = []
    for idx, elo in enumerate(elos):
        # escludo gli altri, per ogni giocatore
        altri = elos[:]
        altri.pop(idx)
        # calcolo l'expected e lo aggiungo alla lista
        expected.append(expected_1_v_others(elo, altri))
    return expected


def new_elos(effective_scores, old_elos, K):
    """
    I: punteggi effettivi, vecchi elo, k
    O: lista di elo aggiornati
    Si appoggia a get_all_expected
    """

    # trovo gli expected
    expected_scores = get_all_expected(old_elos)

    # calcolo gli elo
    return [old_elo + K * (effective_score - expected_score) for expected_score, effective_score, old_elo in zip(expected_scores, effective_scores, old_elos)]


def get_K(playing, total_players, theGreatK):
    """
    I: numero giocanti, numero totale, K di riferimento per giocatori tutti presenti
    O: K da usare
    """
    return theGreatK * playing / total_players


# FUNZIONI MOLTO POCO GENERALI
def aggiornaElo(players, vinte, disputate, k_ref):
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

    number_of_total_players = int(vinte.shape[1])

    for indice_riga in range(vinte.shape[0]):

        # controllo chi era presente
        for idx, player in enumerate(players):
            # se le disputate sono zero
            if (int(disputate.iloc[indice_riga, idx]) == 0):
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
                    float(vinte.iloc[indice_riga, idx]))

        # determino il k da usare
        number_of_playing = len(playing)
        my_k = get_K(number_of_playing, number_of_total_players, k_ref)

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
        nuova_partita.insert(0, vinte.index[indice_riga])

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


def aggiornaVinteDisputate(sheets_dict, players, roundUP=False):
    """
    I:
    sheets_dict: il dizionario di dataframes, generato dall'excel
    players: lista di oggetti Player
    roundUP: per arrotondare le singole vittorie secondo la logica di Dominion
    O:
    dataframe vinte_disputate
    """
    head = ['data']
    for player in players:
        head.append(player.name.lower()+'_vinte')
        head.append(player.name.lower()+'_disputate')

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
        index_incriminato = sheets_dict[key][sheets_dict[key]['GIOCATORE'] == 'CLASSIFICA'].index[0]

        # elimino tutto ciò che c'è dopo
        sheets_dict[key].drop(sheets_dict[key].index[index_incriminato:], inplace=True)

        # elimino due colonne di cui non mi interessa il contenuto
        del sheets_dict[key]['PUNTI']
        del sheets_dict[key]['% PUNTI']

        # giocatori = mydf['GIOCATORE'].unique()

        vinte_disputate_row = []
        for player in players:

            serie_vittorie = sheets_dict[key][sheets_dict[key]['GIOCATORE'] == player.name]['VITTORIE']

            player.vinte = sum(serie_vittorie) if roundUP == False else sum(np.ceil(serie_vittorie))
            player.disputate = len(serie_vittorie)

            vinte_disputate_row.append(player.vinte)
            vinte_disputate_row.append(player.disputate)

        vinte_disputate.loc[giorno] = vinte_disputate_row

    return vinte_disputate


def get_vinte_disputate(vinte_disputate_df, players):

    # converto la colonna data nel formato data
    vinte_disputate_df['data'] = pd.to_datetime(vinte_disputate_df['data'], format='%d/%m/%Y')
    # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior

    # la imposto come indice
    vinte_disputate_df.set_index('data', inplace=True)

    # spacco in due il dataframe
    vinte = vinte_disputate_df.iloc[:, 0::2]
    vinte.columns = [player.name for player in players]
    disputate = vinte_disputate_df.iloc[:, 1::2]
    disputate.columns = vinte.columns

    return vinte, disputate
