import pandas as pd
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, InvalidURI, ServerSelectionTimeoutError
from pathlib import Path
import logging
from typing import List, Dict, Any
import os
from datetime import datetime
from config import config
import hashlib
from collections import defaultdict

#Configuraiton des logs
logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
           handlers=[
                logging.FileHandler('logs/etl_pipeline.log'),  
                logging.StreamHandler()  
            ]     
)
logger = logging.getLogger(__name__)


class ETLPipeline:
    def __init__(self, config):
        # MongoDB credentials
        mongo_username = os.getenv('MONGO_USER')
        mongo_database = self._get_env_variable('MONGO_DATABASE')
        mongo_uri = config.MONGO_URI

        # Debug - Display credentials except password
        logger.info(f"Connecting to MongoDB with user: {mongo_username}")
        logger.info(f"Database: {mongo_database}")
        logger.info(f"URL: {mongo_uri}")

        self.mongo_client = self.connect_to_mongo(mongo_uri)
        self.db = self.mongo_client[mongo_database]
        
        self.column_mapping = {}

        # Tracking state
        self._last_rows = None
        self._last_cols = None

    def connect_to_mongo(self, uri):
        client = MongoClient(uri)
        client.admin.command('ping')
        logger.info("✅ Connection to Mongo successfull !")
        return client

    # Provides an option to fail the process when an important variable is missing.
    @staticmethod
    def _get_env_variable(key, default=None, fail=True):
        value = os.getenv(key, default)
        if value is None and fail:
            raise ValueError(f"Environement variable '{key}' is missing, stopping the process... ")
        return value

    def track_changes(self, df, description=""):
        """Observe les changements SANS modifier le DataFrame"""
        current_rows = df.shape[0]
        current_cols = set(df.columns)
        
        if self._last_rows is not None:
            row_diff = current_rows - self._last_rows
            cols_added = current_cols - self._last_cols
            cols_removed = self._last_cols - current_cols
            
            logger.info(f"{description}: {self._last_rows}→{current_rows} rows ({row_diff:+d})")
            if cols_added:
                logger.info(f"   ➕ Added: {list(cols_added)}")
            if cols_removed:
                logger.info(f"   ➖ Removed: {list(cols_removed)}")
        
        # Sauvegarde pour le prochain check
        self._last_rows = current_rows
        self._last_cols = current_cols

    @staticmethod
    def _parse_name(full_name: str):
        parts = full_name.split()
        name_dict = {"full": full_name}
               
        #Extract title and suffix
        if parts and parts[0] in config.NAME_PREFIXES:
            name_dict["title"] = parts.pop(0)
        if parts and parts[-1] in config.NAME_SUFFIXES:
            name_dict["suffix"] = parts.pop(-1)

        # Extract first and last names
        if len(parts) >= 2:
            name_dict["first"], name_dict["last"] = parts[0], " ".join(parts[1:])
        elif parts:
            name_dict["first"] = parts[0]
    
        return name_dict
    
    @staticmethod
    def _generate_hash_id(values, len=20):
        concat = "|".join(str(v) for v in values)
        return hashlib.sha256(concat.encode()).hexdigest()[:len]
    
    def normalize_column_names(self, df):
        logger.info("Starting column normalization...")
        
        self.column_mapping = {}

        custom_mappings = { "age": "admission_age" }
    
        original_columns = list(df.columns)
        normalized_columns = [col.lower().replace(' ', '_') for col in original_columns]
        final_columns = [custom_mappings.get(col,col) for col in normalized_columns]
    
        # Display whole mapping
        logger.info("📝 Column mapping:")
        for old, new in zip(original_columns, final_columns):
            self.column_mapping[old] = new
            if old != new:
                logger.info(f"   '{old}' → '{new}'")
            else:
                logger.info(f"   '{old}' = '{new}'")
    
        #  Colission detection !!!
        if len(final_columns) != len(set(final_columns)):        
            duplicates = [col for col in final_columns if final_columns.count(col) > 1]
            logger.error(f"❌ COLLISION DETECTED in columns: {set(duplicates)}")
            raise ValueError(f"Column normalization would create duplicates: {set(duplicates)}")
    
        df.columns = final_columns
        logger.info(f"✅ Column normalization complete: {len(original_columns)} columns renamed")
        return df
    
    def ensure_indexes(self):
        """
        Ensures that the necessary indexes are created for the chosen data model,
        based entirely on the central configuration.
        """
        mode = config.DATA_MODELLING_MODE
        logger.info(f"Ensuring indexes for '{mode}' model...")

        # --- Base indexes for the 'patients' collection (common to both modes) ---
        patients_collection_name = config.COLLECTION_PATIENTS
        if patients_collection_name in self.db.list_collection_names():
            patients_collection = self.db[patients_collection_name]
            
            # Create indexes defined in the main INDEXES dictionary
            for index_key in config.INDEXES.get(patients_collection_name, []):
                logger.info(f"  Creating index on '{patients_collection_name}.{index_key}'...")
                patients_collection.create_index(index_key)
        
        # --- Mode-specific indexes ---
        if mode == 'reference':
            hospitalizations_collection_name = config.COLLECTION_HOSPITALIZATIONS
            if hospitalizations_collection_name in self.db.list_collection_names():
                hosp_collection = self.db[hospitalizations_collection_name]
                
                # Create indexes for the hospitalizations collection
                for index_key in config.INDEXES.get(hospitalizations_collection_name, []):
                    logger.info(f"  Creating index on '{hospitalizations_collection_name}.{index_key}'...")
                    hosp_collection.create_index(index_key)

        elif mode == 'embedding':
            # In embedding mode, we add extra indexes to the patients collection
            if patients_collection_name in self.db.list_collection_names():
                patients_collection = self.db[patients_collection_name]

                # Create indexes specific to the embedding model
                for index_key in config.EMBEDDING_INDEXES.get(patients_collection_name, []):
                    logger.info(f"  Creating embedding-specific index on '{patients_collection_name}.{index_key}'...")
                    patients_collection.create_index(index_key)

        logger.info("⚙️ All indexes are set.")

    def clear_collections(self, collection_names):
        """Drops specified collections to ensure a clean slate before loading."""
        logger.info("Clearing target collections ...")
        for name in collection_names:
            logger.info(f"   ➖ Dropping collection: '{name}' ...")
            self.db[name].drop()
        logger.info("✅ Collections cleared successfully.")
    
    def build_documents(self, df, mode):
        """
        Transforms a clean DataFrame into structured documents for different MongoDB modeling strategies,
        using a dynamic column mapping generated during normalization.

        Args:
            df (pd.DataFrame): The transformed and normalized DataFrame.
            mode (str): The modeling strategy ('embedding' or 'reference').

        Returns:
            A dictionary where keys are collection names and values are lists of documents.
        """
        logger.info(f"Structuring documents with '{mode}' model...")

        # Ensure the column mapping has been created by a previous step.
        if not self.column_mapping:
            raise ValueError("Column mapping has not been generated. Run normalize_column_names first.")

        # --- 1. Dynamic Key Translation ---
        # Get original keys from the config and find their current normalized names using the mapping.
        patient_keys_norm = [self.column_mapping[k] for k in config.PATIENT_KEYS]
        hospitalization_keys_norm = [self.column_mapping[k] for k in config.HOSPITALIZATION_KEYS]

        # --- 2. ID Generation ---
        df["hospitalization_id"] = df.apply(
            lambda row: self._generate_hash_id( [row["patient_id"]] + [row[col] for col in hospitalization_keys_norm]), axis=1
        )
         # Build patients & hospitalizations dataframes
        df_patient = df[["patient_id"] + patient_keys_norm].drop_duplicates("patient_id")
        df_patient["name"] = df["name_dict"]  # inject parsed names
        df_hosp = df[["hospitalization_id", "patient_id"] + hospitalization_keys_norm]

        # Build patients & hospitalizations collections
        df_patient = df_patient.rename(columns={"patient_id" : "_id"})
        patients = df_patient.to_dict(orient="records")   

        if mode == 'reference':
            df_hosp = df_hosp.rename(columns={"hospitalization_id": "_id"})
            hospitalizations = df_hosp.to_dict(orient="records")
            return {
                config.COLLECTION_PATIENTS: patients, 
                config.COLLECTION_HOSPITALIZATIONS: hospitalizations
            }    
        
        elif mode == 'embedding':
            # We don't need hospitalization_id for this model
            df_hosp = df_hosp.drop(columns=['hospitalization_id'])
            hospitalizations = df_hosp.to_dict(orient="records")

            # Group hospitalizations by patient
            hospitalizations_grouped = defaultdict(list)

            for hosp in hospitalizations:
                patient_id = hosp.pop("patient_id")
                hospitalizations_grouped[patient_id].append(hosp)

            # Embed into patients
            # We use same name as hospitalization collection for consistency
            embedded_field = config.COLLECTION_HOSPITALIZATIONS
            for patient in patients:
                patient[embedded_field] = hospitalizations_grouped.get(patient["_id"], [])
            
            return { config.COLLECTION_PATIENTS: patients }
        else:
            raise ValueError("Mode must be 'embedding' or 'reference'")

    def extract(self, csv_path):
        """Extract: Read source(csv) file """
        logger.info(f"Extracting data from : {csv_path}")
        df = pd.read_csv(csv_path)
        mem_bytes = df.memory_usage(deep=True).sum()
        logger.info(f"Data extracted: {len(df)} lines, {len(df.columns)} coloumns.Memory usage: {mem_bytes / 1_048_576: .2f} MB")
        return df
    
    def transform(self, df):
        """
        Cleans, normalizes, and structures the data according to the modeling strategy in the config.
        """
        logger.info(f"Transformation started.Initial shape of the dataframe: {df.shape}")   

        # --- 1. CLEANING & FEATURE ENGINEERING 
        # Explicit intention of dataframe update, to avoid copy warning
        df = df.copy()
        self.track_changes(df, "Initial state")

        # Drop full duplicated rows
        df = df.drop_duplicates()   
        self.track_changes(df, "Remove full duplicates")

        # Normalize and tokenize name column
        df["Name"] = df["Name"].str.title()
        df["name_dict"] = df["Name"].apply(self._parse_name)
        self.track_changes(df, "Parsing 'Name' column")

        # Deduplication by checking the age field (anomaly noticed meanwhile my analyse on jupyter notebook)
        # There are around 5 thousand records where every field is identical except "Age"
        df = df.drop_duplicates( subset = ( config.HOSPITALIZATION_KEYS - {"Age"}))
        self.track_changes(df, "Deduplication by excluding Age")

        # Normalize billing amounts abs() + round()        
        df["is_billing_amount_imputed"] = df["Billing Amount"] < 0
        df["Billing Amount"] = df["Billing Amount"].abs().round(2)
        self.track_changes(df, "Normalizing 'Billing Ammount' field")

        # Normalize date fields
        df["Date of Admission"] = pd.to_datetime(df["Date of Admission"])
        df["Discharge Date"] = pd.to_datetime(df["Discharge Date"])
        self.track_changes(df, "Normalizing date values")

        # Generate unique id for patient
        df["Patient Id"] = df.apply(lambda row: self._generate_hash_id( [row[col] for col in config.PATIENT_KEYS] ), axis=1)        
        self.track_changes(df, "Generating patient ids")

        # --- 2. NORMALIZE COLUMN NAMES ---
        # Normalize column names
        df = self.normalize_column_names(df)
        self.track_changes(df, "Normalizing column names")

        # --- 3. BUILD FINAL DOCUMENTS ---
        documents_by_collection = self.build_documents(df, mode=config.DATA_MODELLING_MODE)
        
        logger.info(f"Transformation ended. Produced documents for collections: {list(documents_by_collection.keys())}")
        logger.info(f"Actual shape of the dataframe: {df.shape}")   
        return documents_by_collection
    
    def load(self, collections_data ):
        logger.info("Loading started")
        """
        Loads multiple collections of documents into MongoDB.

        Args:
            collections_data: A dictionary where keys are collection names
                              and values are lists of document records.

        Returns:
            The total number of documents inserted across all collections.
        """        
        logger.info("Loading process started...")
        total_inserted_count = 0

        if not collections_data:
            logger.warning("No data provided to the load method. Nothing to insert.")
            return 0
        
        # Clean database before insertion
        self.clear_collections(config.TARGET_COLLECTIONS)        
        
        # Iterate through each collection name and its list of records
        for collection_name, records in collections_data.items():
                
            # Check if there are records for the current collection
            if not records:
                logger.info(f"Skipping collection '{collection_name}' as it contains no records.")
                continue
                
            logger.info(f"Loading {len(records)} records into collection '{collection_name}'...")
                
            # Get the collection object from the database
            collection = self.db[collection_name]
                
            # Perform the bulk insert operation
            result = collection.insert_many(records)
                
            # Log the success for this specific collection
            inserted_for_this_collection = len(result.inserted_ids)
            total_inserted_count += inserted_for_this_collection
            logger.info(f"  ✅ Successfully inserted {inserted_for_this_collection} documents into '{collection_name}'.")

        logger.info(f"Loading process finished. Total documents inserted: {total_inserted_count}")
        return total_inserted_count
      

    def run_etl(self, csv_path):
        logger.info("====================== PIPELINE START ======================")
        total_inserted_count = 0
        try:
             # Step 1: Extract data from the source file
            source_df = self.extract(csv_path)

            # Step 2: Transform the data : cleaning, normalization and structuring
            collections_to_load = self.transform(source_df)

            # Step 3: Load the resulting documents into their respective collections
            total_inserted_count = self.load(collections_to_load)

            # Step 4 : Ensure indexes
            self.ensure_indexes()

        except FileNotFoundError as e:
            logger.error(f"❌ CRITICAL: Source file not found. Aborting pipeline. Error: {e}")
            # No 'raise', as this is a controlled exit.
        except ValueError as e:
            logger.error(f"❌ CRITICAL: A data validation error occurred. Aborting pipeline. Error: {e}")
        except Exception as e:
            # Catch any other unexpected errors during the process
            logger.error(f"❌ CRITICAL: An unexpected error occurred during pipeline execution: {e}", exc_info=True)
        finally:
            self.mongo_client.close()
            logger.info("MongoDB connection closed.")

        logger.info("======================= PIPELINE END =======================")
        logger.info(f"{total_inserted_count} total documents processed.")

def main():

    if os.path.exists(config.SOURCE_FILE_PATH):
        etl = ETLPipeline(config=config)
        etl.run_etl(config.SOURCE_FILE_PATH)
    else:
        logger.error(f"❌ Source file not found {config.SOURCE_FILE_PATH}.")
        exit(1)


if __name__ == "__main__":
    main()