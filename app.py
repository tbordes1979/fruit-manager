from meteofrance_api import MeteoFranceClient
import datetime
import streamlit as st
from fruit_manager import *
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


st.title("🍇 Dashboard de la Plantation")

inventaire = ouvrir_inventaire()
prix = ouvrir_prix()
tresorerie = ouvrir_tresorerie()

with st.sidebar:
    st.header("🛒 Vendre des Fruits")
    fruit_vendre = st.selectbox(
        "Choisir un fruit", list(inventaire.keys()), key="fruit_vente"
    )
    quantite_vendre = st.number_input("Quantité a vendre", min_value=1, step=1)

    if st.button("Vendre"):
        inventaire, tresorerie, message = vendre(
            inventaire, fruit_vendre, quantite_vendre, tresorerie, prix
        )
        st.success(message["text"])

    st.header("🌱 Récolter des Fruits")
    fruit_recolter = st.selectbox(
        "Choisir un fruit à récolter",
        list(inventaire.keys()),
        key="recolte_individuelle",
    )
    quantite_recolter = st.number_input(
        "Quantité à récolter", min_value=1, step=1, key="quantite_recolte"
    )

    if st.button("Récolter"):
        inventaire, message = recolter(inventaire, fruit_recolter, quantite_recolter)
        st.success(message["text"])


st.header("💰 Trésorerie")
st.metric(label="Montant disponible", value=f"{tresorerie:.2f} $")

st.header("📈 Évolution de la trésorerie")
historique = lire_tresorerie_historique()
if historique:

    df = pd.DataFrame(historique).tail(20)  # Derniers 20 points
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    fig, ax = plt.subplots()
    ax.plot(df["timestamp"], df["tresorerie"], marker="o")
    ax.set_xlabel("Date")
    ax.set_ylabel("Trésorerie ($)")
    ax.set_title("Évolution de la trésorerie")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %H:%M"))
    fig.autofmt_xdate()
    _, mid_col, _ = st.columns([1, 2, 1])
    mid_col.pyplot(fig)
else:
    st.info("Aucune donnée d'historique de trésorerie pour le moment.")


st.header("📦 Inventaire")
# Inventaire sous forme de tableau
st.table(inventaire)
# Inventraire sous forme de graphique
fig, ax = plt.subplots()
# Trier l'inventaire par quantité décroissante
inventaire = dict(sorted(inventaire.items(), key=lambda item: item[1], reverse=True))
ax.bar(inventaire.keys(), inventaire.values(), color="salmon", edgecolor="k")
ax.set_xlabel("Fruit")
ax.set_ylabel("Quantité")
ax.set_title("Inventaire")
st.pyplot(fig)


ecrire_inventaire(inventaire)
ecrire_tresorerie(tresorerie)

# 🔁 Mapping description météo → emoji
emoji_mapping = {
    "Ciel clair": "☀️",
    "Peu nuageux": "🌤️",
    "Ciel voilé": "🌥️",
    "Nuageux": "☁️",
    "Très nuageux": "☁️",
    "Couvert": "☁️",
    "Brume": "🌫️",
    "Brouillard": "🌫️",
    "Pluie faible": "🌦️",
    "Pluie modérée": "🌧️",
    "Pluie forte": "🌧️",
    "Averses de pluie": "🌧️",
    "Orages": "⛈️",
    "Orage fort": "⛈️",
    "Neige": "❄️",
    "Averses de neige": "🌨️",
    "Pluie et neige mêlées": "🌨️",
    "Grêle": "🌩️",
}

# Client météo
client = MeteoFranceClient()
places = client.search_places("Blanquefort")
place = places[0]
forecast = client.get_forecast(place.latitude, place.longitude, language="fr")
tomorrow = datetime.date.today() + datetime.timedelta(days=1)

# Recherche de la météo de demain
# Recherche de la météo de demain
st.header("🌤️ Météo de demain à Blanquefort")

trouve = False
for day in forecast.daily_forecast:
    day_date = datetime.datetime.fromtimestamp(day["dt"]).date()
    if day_date == tomorrow:
        temp_min = day["T"]["min"]
        temp_max = day["T"]["max"]
        description = day["weather12H"]["desc"]
        icon_code = day["weather12H"]["icon"]
        icon_url = f"https://meteofrance.com/modules/custom/mf_tools_common_theme/images/weather/{icon_code}.svg"
        emoji = emoji_mapping.get(description, "❓")

        st.markdown(f"📍 **{place.name} – {tomorrow.strftime('%A %d %B')}**")
        st.markdown(f"{emoji} **{description}**")
        st.markdown(f"🌡️ Température min : **{temp_min}°C**")
        st.markdown(f"🌡️ Température max : **{temp_max}°C**")
        st.image(icon_url, width=80)
        trouve = True
        break

if not trouve:
    st.warning("Météo de demain indisponible.")
