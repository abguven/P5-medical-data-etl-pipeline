# 🚀 Projet 5: Maintenez et documentez un système de stockage des données sécurisé et performant

Ce projet a pour objectif de migrer un jeu de données de patients, initialement au format CSV, vers une base de données NoSQL MongoDB. La solution est entièrement conteneurisée avec Docker pour garantir sa portabilité et sa reproductibilité.

## 🎯 Contexte de la Mission

La mission, confiée par l'entreprise DataSoluTech, vise à fournir à un client une solution de stockage de données plus moderne et scalable horizontalement pour faire face à des problèmes de performance avec leurs systèmes actuels.

---

## 🔑 Concepts Clés de MongoDB

Pour comprendre la structure de notre base de données cible, il est essentiel de maîtriser trois concepts fondamentaux de MongoDB. L'analogie la plus simple est celle d'une armoire de bureau.

| Concept Relationnel (SQL) | Concept MongoDB (NoSQL) | Analogie |
| :--- | :--- | :--- |
| Base de Données | **Database** | 🗄️ L'armoire entière |
| Table | **Collection** | 🗂️ Un tiroir de l'armoire |
| Ligne / Enregistrement | **Document** | 📄 Un dossier dans un tiroir |

### 1. Database (Base de Données)
- **Définition :** C'est le conteneur principal qui regroupe toutes les collections liées à notre projet.
- **Notre projet :** Nous utilisons une base de données unique nommée `medical_db`.

### 2. Collection
- **Définition :** C'est un regroupement de documents, similaire à une table en SQL mais avec un schéma flexible. Cela signifie que les documents d'une même collection n'ont pas besoin d'avoir exactement la même structure.
- **Notre projet :** Nous avons une collection principale nommée `patients` qui contiendra tous les enregistrements de nos patients.

### 3. Document
- **Définition :** C'est l'unité de stockage de base dans MongoDB. Il s'agit d'un enregistrement au format BSON (un JSON binaire optimisé), composé de paires clé-valeur.
- **Notre projet :** Chaque ligne de notre fichier CSV d'origine est transformée en un document. Voici un exemple :

```json
{
  "_id": "62e8c5d9f7e4a9b8d8f1e2a3",
  "name": "Bobby Jackson",
  "age": 30,
  "gender": "Male",
  "blood_type": "B-",
  "medical_condition": "Cancer",
  "date_of_admission": "2024-01-31T00:00:00.000Z",
  "billing_amount": 18856.28,
  "billing_amount_imputed": false
}
```
---

# 🚀 Installation et Lancement

# Comment utiliser :
## 1. Préparer les données

## 2. Lancer le pipeline complet

````sh
# Lancer tous les services
docker-compose up --build

# En arrière-plan
docker-compose up -d --build
````

## 3. Monitoring et debug
````sh
# Voir les logs de votre ETL
docker-compose logs etl-app

# Accéder à MongoDB via l'interface web
# http://localhost:8081 (admin/admin123)

# Entrer dans le conteneur pour debug
docker-compose exec etl-app bash
````





---
# 🛠️ Structure du Projet