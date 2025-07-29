from meteofrance_api import MeteoFranceClient
import datetime
import streamlit as st
from fruit_manager import *
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import locale

locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")  # Force le français
aujourd_hui = datetime.date.today()
date_aujourd_hui = aujourd_hui.strftime("%A %d %B %Y").capitalize()

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
with st.sidebar:
    st.markdown(f"📅 **{date_aujourd_hui}**")
    ville = st.text_input("Entrez le nom d'une ville", value="Paris")

if ville:
    places = client.search_places(ville)
else:
    st.error("❌ Ville introuvable.")
place = places[0]
forecast = client.get_forecast(place.latitude, place.longitude, language="fr")
tomorrow = datetime.date.today() + datetime.timedelta(days=1)

# Recherche de la météo de demain
date_str = tomorrow.strftime("%d %B")
st.title(f"🌤️ Météo à {ville} – {date_str}")

trouve = False
for day in forecast.daily_forecast:
    day_date = datetime.datetime.fromtimestamp(day["dt"]).date()
    if day_date == tomorrow:
        temp_min = day["T"]["min"]
        temp_max = day["T"]["max"]
        description = day["weather12H"]["desc"]
        icon_code = day["weather12H"]["icon"]
        emoji = emoji_mapping.get(description, "❓")

        # nouvelles données
        precip_24h = day["precipitation"]["24h"]
        sunrise = datetime.datetime.fromtimestamp(day["sun"]["rise"]).strftime("%H:%M")
        sunset = datetime.datetime.fromtimestamp(day["sun"]["set"]).strftime("%H:%M")
        uv = day.get("uv", "N/A")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"☀️ Lever : **{sunrise}**")
    st.markdown(f"🌃 Coucher : **{sunset}**")
with col2:
    st.markdown(f"❄️ Min : **{temp_min}°C**")
    st.markdown(f"🔥️ Max : **{temp_max}°C**")
with col3:
    st.markdown(f"💧 Pluie (24h) : **{precip_24h} mm**")
    st.markdown(f"🔆 UV max : **{uv}**")

trouve = True

if not trouve:
    st.warning("Météo de demain indisponible.")

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
