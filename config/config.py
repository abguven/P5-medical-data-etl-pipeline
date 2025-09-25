# config/config.py
from pathlib import Path
from dotenv import load_dotenv
import os

# Check if we are not in docker (heuristic: /.dockerenv exists inside docker)
if not Path("/.dockerenv").exists():
    print("NOT A DOCKER ENV")
    _is_docker_env = False
    load_dotenv(".env.local")
else:
    print("RUNNING IN A DOCKER ENV")
    _is_docker_env = True


NAME_PREFIXES = {"Mr.", "Mrs.", "Ms.", "Miss", "Dr.", "Prof.", "Sir"}
NAME_SUFFIXES = {"Jr.", "Sr.", "II", "III", "IV", "MD", "DDS", "DVM", "PhD", "Esq."}

PATIENT_KEYS = { "Name", "Gender", "Blood Type" }

HOSPITALIZATION_KEYS = {
            'Hospital','Date of Admission','Discharge Date',
            'Medical Condition','Room Number','Doctor',
            'Admission Type','Medication','Test Results',
            'Age','Insurance Provider','Billing Amount'
}

# Directories
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
LOG_DIR = Path(os.getenv("LOG_DIR", "./app/logs"))
SOURCE_FILE_PATH = DATA_DIR / "healthcare_dataset.csv" 


# DATABASE SETTINGS ********************************************************************
# Data modeling strategy for MongoDB
DATA_MODELLING_MODE = "embedding" # 'embedding' or 'reference'

# Mongo credentials
MONGO_USER = os.getenv("MONGO_USER", "root")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "password")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB = os.getenv("MONGO_DATABASE", "etl_database")
# Build URI dynamically
if _is_docker_env:
    MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

# Target collection names
COLLECTION_PATIENTS = "patients"
COLLECTION_HOSPITALIZATIONS = "hospitalizations"

TARGET_COLLECTIONS = [COLLECTION_PATIENTS, COLLECTION_HOSPITALIZATIONS]

# Definition of desired indexes for each collection
# This structure will allow us to create indexes dynamically
INDEXES = {
    COLLECTION_PATIENTS: [
        # Key: the field to index (in dot notation for sub-documents)
        # Value (optional): the index type (empty for default)
        "name.last",
        "blood_type"
    ],
    COLLECTION_HOSPITALIZATIONS: [
        "patient_id"
    ]
}
# Specific indexes for 'embedding' mode
# We add them only in this mode
EMBEDDING_INDEXES = {
    COLLECTION_PATIENTS: [
        f"{COLLECTION_HOSPITALIZATIONS}.medical_condition"
    ]
}
