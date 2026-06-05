import streamlit as st
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import io

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Pilote IA & Trésorerie", layout="wide", page_icon="💰")

st.title("📦 Pilote IA : Optimisation des Stocks & Analyse Financière (USD)")
st.markdown("Pilotez votre logistique et visualisez l'argent (USD) économisé grâce aux prévisions de l'IA.")

# --- BARRE LATÉRALE : PARAMÈTRES LOGISTIQUES & FINANCIERS ---
st.sidebar.header("🛠️ Paramètres Logistiques")
delai_fournisseur = st.sidebar.slider("Délai de livraison fournisseur (jours)", min_value=1, max_value=30, value=5)
taux_service_option = st.sidebar.selectbox(
    "Niveau de sécurité (Taux de service)",
    options=["90% (Risque modéré)", "95% (Standard)", "99% (Sécurité maximale)"],
    index=1
)
taux_service_map = {"90% (Risque modéré)": 1.28, "95% (Standard)": 1.65, "99% (Sécurité maximale)": 2.33}
z_score = taux_service_map[taux_service_option]

st.sidebar.header("💵 Paramètres Financiers (USD)")
cout_achat = st.sidebar.number_input("Coût d'achat unitaire d'un produit ($)", min_value=0.1, value=15.0)
prix_vente = st.sidebar.number_input("Prix de vente unitaire d'un produit ($)", min_value=0.1, value=45.0)
cout_stockage_annuel_pct = st.sidebar.slider("Coût de stockage annuel (% de la valeur du produit)", min_value=5, max_value=50, value=20)

# --- CHARGEMENT DES DONNÉES ---
st.header("📊 Historique des Ventes")
fichier_uploade = st.file_uploader("Importez vos ventes (CSV ou Excel)", type=["csv", "xlsx"])

if fichier_uploade is not None:
    if fichier_uploade.name.endswith('.csv'):
        df_ventes = pd.read_csv(fichier_uploade, sep=';' if ';' in fichier_uploade.getvalue().decode('utf-8') else ',')
    else:
        df_ventes = pd.read_excel(fichier_uploade)
    st.success("✅ Données réelles chargées !")
else:
    st.info("💡 Mode simulation activé.")
    np.random.seed(42)
    dates = pd.date_range(start="2025-01-01", periods=400, freq="D")
    ventes = np.random.randint(10, 100, size=400) + np.sin(np.arange(400)/10)*20
    df_ventes = pd.DataFrame({"Date": dates, "Ventes_Reelles": ventes})

# Traitement des données pour l'IA
df_ventes['Date'] = pd.to_datetime(df_ventes['Date'])
df_ventes = df_ventes.sort_values('Date').reset_index(drop=True)
df_ventes['Mois'] = df_ventes['Date'].dt.month
df_ventes['Jour_Semaine'] = df_ventes['Date'].dt.dayofweek
df_ventes['Ventes_Veille'] = df_ventes['Ventes_Reelles'].shift(1)
df_clean = df_ventes.dropna()

# --- ENTRAÎNEMENT DE L'IA ---
X = df_clean[['Mois', 'Jour_Semaine', 'Ventes_Veille']]
y = df_clean['Ventes_Reelles']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
dates_test = df_clean['Date'].iloc[X_test.index]

modele_ia = XGBRegressor(n_estimators=100, learning_rate=0.05, random_state=42)
modele_ia.fit(X_train, y_train)

predictions = modele_ia.predict(X_test)
demande_moyenne = np.mean(predictions)
erreurs = y_test - predictions
ecart_type_erreurs = np.std(erreurs)

# --- CALCULS LOGISTIQUES & SIMULATION FINANCIÈRE ---
stock_securite_ia = z_score * ecart_type_erreurs * np.sqrt(delai_fournisseur)
point_de_commande_ia = (demande_moyenne * delai_fournisseur) + stock_securite_ia

# Simulation empirique d'une gestion classique sans IA (sur-stockage de sécurité forfaitaire)
stock_securite_classique = demande_moyenne * delai_fournisseur * 0.5 
surstock_evite_unites = max(0, stock_securite_classique - stock_securite_ia)

# Calcul des gains financiers directs (USD)
cout_stockage_journalier_unite = (cout_achat * (cout_stockage_annuel_pct / 100)) / 365
economie_stockage_usd = surstock_evite_unites * cout_stockage_journalier_unite * len(X_test)
marge_unitaire = prix_vente - cout_stockage_journalier_unite

# --- TABLEAU DE BORD DE DÉCISION ---
st.header("🎯 Indicateurs Opérationnels & Trésorerie")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Demande Prédite (Jour)", f"{demande_moyenne:.1f} u.")
with col2:
    st.metric("Stock de Sécurité", f"{stock_securite_ia:.1f} u.")
with col3:
    st.metric("🚨 POINT DE COMMANDE", f"{point_de_commande_ia:.1f} u.")
with col4:
    st.metric("💰 Économies Estimées (Période)", f"${economie_stockage_usd:.2f} USD", delta=f"${marge_unitaire:.2f} marge/u")

# --- BOUTON DE TÉLÉCHARGEMENT EXCEL ---
st.subheader("📥 Générer le plan de réapprovisionnement")

# Création du fichier Excel virtuel en mémoire
rapport_df = pd.DataFrame({
    "Indicateur Logistique": ["Demande Quotidienne Prédite", "Stock de Sécurité Requis", "POINT DE COMMANDE (Alerte)", "Gain Financier Estimé (USD)"],
    "Valeur": [round(demande_moyenne, 2), round(stock_securite_ia, 2), round(point_de_commande_ia, 2), round(economie_stockage_usd, 2)],
    "Unité": ["Unités / Jour", "Unités en entrepôt", "Seuil critique d'unités", "Dollars USD"]
})

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    rapport_df.to_excel(writer, index=False, sheet_name='Plan_Logistique')
buffer.seek(0)

st.download_button(
    label="📥 Télécharger le Rapport Logistique (.xlsx)",
    data=buffer,
    file_name="plan_approvisionnement_ia.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- GRAPHES ---
st.header("📈 Courbes de Suivi Épidémique des Ventes")
fig, ax = plt.subplots(figsize=(12, 3.5))
ax.plot(dates_test, y_test.values, label="Ventes Réelles", color="#1f77b4", alpha=0.5)
ax.plot(dates_test, predictions, label="Prévisions de votre IA", color="#ff7f0e", linewidth=2)
ax.axhline(y=point_de_commande_ia, color='r', linestyle=':', label="Seuil Point de Commande")
ax.set_ylabel("Unités")
ax.legend()
ax.grid(True, linestyle="--", alpha=0.5)
st.pyplot(fig)
