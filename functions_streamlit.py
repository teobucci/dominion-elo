import altair as alt
import streamlit as st
import pandas as pd


def plotEloDataframe(elo_df, vinte, disputate):

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
        tooltip=[alt.Tooltip(c, type='quantitative', format='.1f') for c in columns]
    ).add_selection(selection)

    grafico = alt.layer(lines, points, rule).properties(
        width=800,
        height=400
    ).interactive()
    # primo plot
    st.markdown("### Punteggi")
    st.altair_chart(grafico)

    mostra_elo_df = st.beta_expander("Mostra il dataframe degli Elo", expanded=False)
    mostra_elo_df.write(elo_df)

    # elo_df.plot(grid=True)
    # plt.legend(loc='center right', bbox_to_anchor=(1, 0.5))

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

    # creo la classifica
    classifica = elo_df.iloc[-1]

    # la sorto dal valore più alto al più piccolo
    classifica.sort_values(ascending=False, inplace=True)

    # aggiungo le medaglie
    indexes = classifica.index
    classifica.rename(index={
        indexes[0]: '🥇 '+indexes[0],
        indexes[1]: '🥈 '+indexes[1],
        indexes[2]: '🥉 '+indexes[2]
    }, inplace=True)

    # pip install tabulate
    st.markdown(classifica.to_markdown())

    st.markdown("### Ulteriori statistiche (cioè funzioni dei dati)")

    # WinRate puntuale e cumulativo DFs
    winrate_puntuale = vinte.div(disputate)
    # winrate_puntuale.fillna(0, inplace=True)
    winrate_cumulativo = vinte.cumsum() / disputate.cumsum()

    statistiche = pd.DataFrame(columns=elo_df.columns)

    statistiche.loc['Media'] = elo_df.mean().round(2)
    statistiche.loc['Vinte'] = vinte.sum().values
    statistiche.loc['Disputate'] = disputate.sum().values
    statistiche.loc['WinRate'] = (statistiche.loc['Vinte'] / statistiche.loc['Disputate']).round(3)
    statistiche.loc['Massimo ELO'] = elo_df.max().round(2)
    statistiche.loc['Minimo ELO'] = elo_df.min().round(2)
    # statistiche.loc['Raggiunto il'] = elo_df.idxmax(axis=0)
    statistiche.loc['Delta'] = (elo_df.max()-elo_df.min()).round(2)

    # PRIMO PER
    serie_primo = elo_df.iloc[1:, :].idxmax(axis=1)
    for idx, value in serie_primo.value_counts().items():
        statistiche.loc['Primo per', idx] = value

    # ININTERROTTAMENTE PER
    # https://stackoverflow.com/questions/26911851/how-to-use-pandas-to-find-consecutive-same-data-in-time-series
    # https://stackoverflow.com/questions/27626542/counting-consecutive-positive-value-in-python-array
    mydf = pd.DataFrame(data=serie_primo, columns=['firstplayer'], index=vinte.index)
    mydf['subgroup'] = (mydf['firstplayer'] != mydf['firstplayer'].shift(1)).cumsum()
    # mydf['subgroup'].value_counts()
    statistiche.loc['Ininterrottamente'] = 0

    # st.write(serie_primo)
    # st.write(statistiche)
    # st.write(mydf)
    for idx, value in mydf['subgroup'].value_counts().items():
        # trovo il nome
        nome = mydf[mydf['subgroup'] == idx].iloc[0, 0]
        # se il numero di volte consecutivo attuale è più piccolo di quello che trovo
        if statistiche.loc['Ininterrottamente', nome] < value:
            statistiche.loc['Ininterrottamente', nome] = value

    # chi non è mai stato primo ha un NaN
    statistiche.fillna(0, inplace=True)

    # prendo dal primo gennaio TODO
    MVPs = elo_var.iloc[1:, :].idxmax(axis=1).value_counts()
    mong = elo_var.iloc[1:, :].idxmin(
        axis=1).value_counts()  # prendo dal primo gennaio

    for idx, value in MVPs.items():
        statistiche.loc['MPVs', idx] = value

    for idx, value in mong.items():
        statistiche.loc['Mongolini', idx] = value

    statistiche['TOP PLAYER'] = statistiche.idxmax(axis=1)

    # il top player dell'elo minimo non è quello che ha il massimo elo minimo, quindi devo cambiarlo manualmente
    statistiche.loc['Minimo ELO', 'TOP PLAYER'] = statistiche.loc['Minimo ELO'].iloc[:-1].astype(float).idxmin()

    st.write(statistiche)

    # mostro DataFrame del WinRate
    mostra_winrate_puntuale = st.beta_expander("Mostra il WinRate puntuale", expanded=False)
    mostra_winrate_puntuale.write(winrate_puntuale)

    mostra_winrate_cum = st.beta_expander("Mostra il WinRate cumulativo", expanded=False)
    mostra_winrate_cum.write(winrate_cumulativo)

    # Plotto il WinRate cumulativo
    st.markdown("WinRate cumulativo")
    st.line_chart(winrate_cumulativo.iloc[1:])
