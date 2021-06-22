import random


def get_rr_rounds(players):
    """
    Bisogna passare una lista, tipo
    players = ["Player1", "Player2", "Player3","Player4", "Player5", "Player6"]
    e restituisce una lista dei turni, dove ciascun turno è una lista di partite
    """
    # se non sono pari, aggiungo un dummy
    if len(players) % 2:
        players.append('DUMMY')

    n = len(players)

    matchs = []
    rounds = []

    # per assicurarmi che negli stessi match non inizi sempre lo stesso giocatore
    discriminante = random.choice([0, 1])

    for round in range(1, n):

        for i in range(n//2):
            # l'i-esimo a sinistra e a destra o viceversa, TODO assicurarsi il first player
            if (round % 2 == discriminante):
                matchs.append((players[i], players[n - 1 - i]))
            else:
                matchs.append((players[n - 1 - i], players[i]))

        # giro: nella posizione 1 (la seconda) inserisco l'ultimo elemento
        # e contemporaneamente lo tolgo come ultimo elemento
        players.insert(1, players.pop())

        # inserisco nei rounds
        rounds.append(matchs)

        # resetto i matchs
        matchs = []
    return rounds


"""

#il codice qui sotto viene svolto ogni volta che si fa import,
#per evitarlo basta scommentare la riga sotto e indentare
#if __name__=='__main__':

players = ["Player1", "Player2", "Player3", "Player4", "Player5", "Player6"]

for index, player in enumerate(players):
    print(f"{index} corrisponde a {player}")

turni = get_rr_rounds(players)
for turno in turni:
    print(turno)
"""
