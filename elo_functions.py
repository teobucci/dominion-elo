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
