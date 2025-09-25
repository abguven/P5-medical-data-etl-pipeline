# Importation du client MongoDB
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def main():
    """
    Fonction principale pour démontrer les opérations CRUD sur MongoDB.
    """
    # --- 1. CONNEXION À LA BASE DE DONNÉES LOCALE (MONGODB LOCAL) ---       
    connection_string = "mongodb://localhost:27017/"
    mdb_client = MongoClient(connection_string)

    # Vérifier que la connexion a réussi
    try:
        mdb_client.admin.command('ping')
        print("✅ Connection à la MongoDB local réussie !")
    except ConnectionFailure:
        print("❌ Impossible de se connecter à MongoDB local.?")
        return 

    # Sélectionner la base de données et la collection
    # Si la base de données ou la collection n'existent pas, MongoDB les créera automatiquement à la première insertion.
    database = mdb_client['medical_db_examples']
    patients_collection = database['patients']

    # --- Nettoyage : S'assurer que la collection est vide avant chaque exécution ---
    print("\n🧹 Nettoyage de la collection 'patients'...")
    patients_collection.delete_many({})


    # --- 2. CREATE (Créer un document) ---
    # Un exemple simplifié de notre dataset
    sample_patient = {
        "name": "Jane Doe",
        "age": 42,
        "gender": "Female",
        "medical_condition": "Hypertension",
        "billing_amount": 1250.75
    }
    
    print("\n--- CREATE ---")
    insert_result = patients_collection.insert_one(sample_patient)
    print(f"🗄️ Patient 'Jane Doe' inséré avec l'ID : {insert_result.inserted_id}")

    # --- 3. READ (Lire un document) ---
    print("\n--- READ ---")
    found_patient = patients_collection.find_one({"name": "Jane Doe"})
    if found_patient:
        print("🔎 Patient trouvé :")
        print(found_patient)
    else:
        print("Patient non trouvé.")


    # --- 4. UPDATE (Mettre à jour un document) ---
    print("\n--- UPDATE ---")
    # On met à jour la condition médicale de Jane Doe
    update_result = patients_collection.update_one(
        {"name": "Jane Doe"},
        {"$set": {"medical_condition": "Controlled Hypertension"}}
    )
    print(f"🔢 Nombre de documents mis à jour : {update_result.modified_count}")
    
    # Vérifions le résultat en relisant le document
    updated_patient = patients_collection.find_one({"name": "Jane Doe"})
    print("🩺 Patient après mise à jour :")
    print(updated_patient)


    # --- 5. DELETE (Supprimer un document) ---
    print("\n--- DELETE ---")
    # On supprime le patient que nous venons de créer
    delete_result = patients_collection.delete_one({"name": "Jane Doe"})
    print(f"🗑️ Nombre de documents supprimés : {delete_result.deleted_count}")

    # Vérifions qu'il n'existe plus
    deleted_patient = patients_collection.find_one({"name": "Jane Doe"})
    if not deleted_patient:
        print("✅ Le patient 'Jane Doe' a bien été supprimé.")

    # Fermer la connexion
    mdb_client.close()

# Point d'entrée du script
if __name__ == "__main__":
    main()