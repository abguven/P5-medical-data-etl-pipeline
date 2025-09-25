# 🚀 Projet 5: Pipeline ETL pour Données Médicales vers MongoDB

Ce projet met en place un pipeline ETL (Extract, Transform, Load) complet pour migrer un jeu de données de patients depuis un fichier CSV vers une base de données NoSQL MongoDB. La solution est entièrement conteneurisée avec Docker et Docker Compose pour garantir une portabilité et une reproductibilité parfaites.

## 🎯 Contexte de la Mission

La mission, confiée par l'entreprise DataSoluTech, vise à fournir à un client une solution de stockage de données moderne, performante et scalable pour gérer l'historique médical de ses patients. Le pipeline développé nettoie, structure et charge les données, tout en mettant en place un système d'authentification sécurisé.

---

## 🏗️ Architecture de la Solution

La solution est orchestrée par Docker Compose et se compose de trois services principaux :

- **`etl-app`**: Un conteneur Python qui exécute notre script ETL. Il lit le CSV, le transforme, et charge les données dans MongoDB.
- **`mongo`**: Le service de base de données MongoDB, configuré avec un utilisateur administrateur et un utilisateur "analyste" en lecture seule.
- **`mongo-express`**: Une interface web d'administration pour visualiser et interroger facilement la base de données.

Les services communiquent entre eux sur un réseau Docker privé pour plus de sécurité.

---

## 💾 Modélisation des Données

Suite à une analyse approfondie du jeu de données, nous avons découvert que chaque ligne du CSV représentait une **hospitalisation** et non un patient unique. Le pipeline a donc été conçu pour supporter deux stratégies de modélisation NoSQL, configurables via la variable `DATA_MODELLING_MODE` dans le fichier `.env`.

### 1. Modèle `embedding` (par défaut)
Ce modèle est optimisé pour les lectures. Chaque document représente un patient unique et contient un tableau imbriqué de toutes ses hospitalisations.

**Exemple de document `patients`:**
```json
{
  "_id": "hash_du_patient",
  "name": {
    "full": "Mr. Brandon Johnson Jr.",
    "title": "Mr.", 
    "first": "Brandon",
    "last": "Johnson",
    "suffix": "Jr.", 
    // Note: Les champs 'title' et 'suffix' sont optionnels.
  },
  "gender": "Male",
  "blood_type": "B+",
  "hospitalizations": [
    {
      "test_results": "Normal",
      "hospital": "Sons and Miller",
      "admission_type": "Urgent",
      "date_of_admission": "2023-11-12T00:00:00Z",
      "discharge_date": "2023-11-13T00:00:00Z",
      "insurance_provider": "Blue Cross",
      "admission_age": 79,
      "medication": "Paracetamol",
      "billing_amount": 6612.15,      
      "medical_condition": "Cancer",
      "doctor": "Amber Payne",
      "room_number": 328
    },
    {
      "admission_age": 83,
      "date_of_admission": "2023-11-12T00:00:00Z",
      "doctor": "Amber Payne",
      // ... autres champs du séjour (chambre, médication, etc.)
    }
  ]
}
```

### 2. Modèle `reference`
Ce modèle normalise les données dans deux collections distinctes, ce qui est idéal pour les environnements avec de nombreuses mises à jour.
- **`patients`**: Contient les informations uniques de chaque patient.
- **`hospitalizations`**: Contient les détails de chaque séjour, avec un champ `patient_id` faisant référence à la collection `patients`.

---

## 🚀 Installation et Lancement

Suivez ces étapes pour lancer le projet complet.

### 1. Prérequis
- [Docker](https://www.docker.com/products/docker-desktop/) et Docker Compose installés.
- Git installé.

### 2. Cloner le Dépôt
```bash
git clone https://github.com/abguven/P5-medical-data-etl-pipeline.git
cd P5-medical-data-etl-pipeline
```

### 3. Configurer les Variables d'Environnement
Le projet utilise des variables d'environnement pour gérer les secrets et la configuration.

Copiez le fichier d'exemple et personnalisez-le si nécessaire (notamment les mots de passe).
```bash
cp .env.example .env
```
Ouvrez le fichier `.env` et modifiez les valeurs `MONGO_PASSWORD` et `WEB_PASSWORD`. Vous pouvez aussi changer le `DATA_MODELLING_MODE` pour tester les deux stratégies.

### 4. Lancer le Pipeline Complet
Cette commande va construire l'image Python, démarrer la base de données, exécuter le script ETL, puis lancer l'interface web.

```bash
# Lancer tous les services en arrière-plan
docker-compose up -d --build
```
Le pipeline s'exécute automatiquement au démarrage. La première exécution peut prendre un peu de temps pour télécharger les images et installer les dépendances.

---

## 🛠️ Utilisation et Monitoring

### Accéder aux Données
- **Mongo Express (Interface Web)**: Ouvrez votre navigateur et allez sur [http://localhost:8081](http://localhost:8081).
  - Utilisez les identifiants `WEB_USERNAME` et `WEB_PASSWORD` définis dans votre fichier `.env` pour vous connecter.

### Monitoring et Debug
```bash
# Voir les logs en temps réel de tous les services
docker-compose logs -f

# Voir les logs spécifiques du script ETL
docker-compose logs etl-app

# Entrer dans le conteneur ETL pour un debug avancé
docker-compose exec etl-app bash
```

### Arrêter les Services
Pour arrêter tous les conteneurs :
```bash
docker-compose down
```
Pour un nettoyage complet (incluant la suppression du volume de données MongoDB) :
```bash
docker-compose down -v
```

---

## 🧪 Scripts d'Exploration

Le dossier `notebooks_and_tests/` contient des scripts utilisés durant la phase de développement pour valider certains points de la mission.
- **`crud_examples.py`**: Démontre les opérations CRUD de base sur une instance MongoDB locale.