# Influençons.com — Blog Flask

## 🚀 Déploiement sur Render

### Étape 1 — Préparer le repo GitHub
1. Crée un nouveau dépôt GitHub (public ou privé)
2. Upload tous les fichiers de ce dossier
3. Assure-toi que la structure est respectée

### Étape 2 — Créer le service sur Render
1. Va sur [render.com](https://render.com) et connecte-toi
2. Clique **New → Web Service**
3. Connecte ton repo GitHub
4. Configure :
   - **Name** : influencons
   - **Environment** : Python 3
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn wsgi:app`

### Étape 3 — Créer la base de données PostgreSQL
1. Dans Render, clique **New → PostgreSQL**
2. Nomme-la `influencons-db`
3. Copie le **Internal Database URL**

### Étape 4 — Variables d'environnement
Dans ton Web Service sur Render, ajoute :

| Variable | Valeur |
|---|---|
| `DATABASE_URL` | *(l'URL PostgreSQL copiée)* |
| `SECRET_KEY` | *(une clé aléatoire longue)* |
| `ADMIN_EMAIL` | ton email admin |
| `ADMIN_PASSWORD` | ton mot de passe admin |

### Étape 5 — Déployer !
Clique **Manual Deploy → Deploy latest commit**

---

## 🔐 Accès Admin
- URL : `https://ton-site.onrender.com/admin`
- Email et mot de passe définis dans les variables d'environnement

## 📁 Structure du projet
```
influencons/
├── app/
│   ├── __init__.py          # Config Flask
│   ├── models.py            # Base de données
│   ├── routes/
│   │   ├── main.py          # Routes publiques
│   │   └── admin.py         # Routes admin
│   └── templates/
│       ├── base.html        # Template de base (design maquette)
│       ├── index.html       # Page d'accueil
│       ├── article.html     # Article individuel
│       ├── articles.html    # Liste articles
│       └── admin/           # Interface admin
├── wsgi.py                  # Point d'entrée
├── requirements.txt         # Dépendances Python
├── Procfile                 # Config Gunicorn
├── render.yaml              # Config Render (optionnel)
└── .env.example             # Variables d'environnement exemple
```

## 💻 Développement local
```bash
# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Créer le fichier .env
cp .env.example .env
# Édite .env avec tes valeurs

# Lancer le serveur
python wsgi.py
```

Accède au site sur http://localhost:5000
