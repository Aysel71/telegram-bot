# check_connection.py
# Script to check Firebase connection

import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def check_firebase_connection():
    """Check connection to Firebase Firestore"""
    try:
        print("Starting Firebase connection test...")
        
        # Path to your service account credentials file
        cred_path = "recsys-4d590-firebase-adminsdk-fbsvc-217f8ac876.json"
        
        # Check if the credentials file exists
        if not os.path.exists(cred_path):
            logging.error(f"Credentials file not found: {cred_path}")
            print(f"Error: Firebase credentials file not found at {cred_path}")
            return False
        
        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            print("Initializing Firebase with credentials...")
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logging.info("Firebase initialized successfully")
        
        # Get Firestore client
        print("Getting Firestore client...")
        db = firestore.client()
        logging.info("Firestore client obtained")
        
        # Test connection by writing and reading a test document
        test_collection = 'test_connection'
        test_doc_id = 'test_document'
        
        # Write test document
        print("Writing test document...")
        test_ref = db.collection(test_collection).document(test_doc_id)
        test_ref.set({
            'timestamp': firestore.SERVER_TIMESTAMP,
            'message': 'Connection test successful'
        })
        logging.info("Test document written")
        
        # Read test document
        print("Reading test document...")
        test_doc = test_ref.get()
        if test_doc.exists:
            print(f"Test document read successfully: {test_doc.to_dict()}")
            logging.info(f"Test document read: {test_doc.to_dict()}")
        else:
            logging.error("Test document not found!")
            print("Error: Test document not found!")
            return False
        
        # Delete test document for cleanup
        print("Cleaning up test document...")
        test_ref.delete()
        logging.info("Test document deleted")
        
        return True
    
    except Exception as e:
        logging.error(f"Error testing connection: {e}")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("\n===== FIREBASE CONNECTION TEST =====\n")
    if check_firebase_connection():
        print("\n✅ Firebase connection established successfully!")
        print("   You can now run your bot.\n")
    else:
        print("\n❌ Failed to connect to Firebase.")
        print("   Please check your credentials file and settings.\n")