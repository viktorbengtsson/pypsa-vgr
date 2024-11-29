import os
import sys
from pathlib import Path
import json
import pandas as pd
import ibm_boto3
from ibm_botocore.client import Config
from io import BytesIO
from pathlib import Path
import streamlit as st

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

from paths import api_path, dashboard_path

# Check environment variables for API type

api_type = os.getenv("API", "local")

# Local or Streamlit cloud data root

def set_data_root():
    if "DATA_ROOT" in st.secrets:
        # Manually set in Community Cloud Secrets
        return st.secrets["DATA_ROOT"]
    else:
        return api_path

# IBM COS configuration

if api_type == 'ibm':
    with (dashboard_path / 'apikey.json').open("r") as file:
        credentials = json.load(file)

    cos = ibm_boto3.client(
        "s3",
        ibm_api_key_id=credentials['apikey'],
        ibm_service_instance_id="46e90cd7-db18-4c5a-8a1d-87d95250c725",
        config=Config(signature_version="oauth"),
        endpoint_url="https://s3.eu-de.cloud-object-storage.appdomain.cloud"
    )

    bucket_name = 'et-vgr-data'
elif api_type == 'local':
    data_root = set_data_root()

# Utility functions

def read_csv(file_key, **kwargs):
    if api_type == 'ibm':
        """Read a CSV file directly from IBM COS into a pandas DataFrame."""
        try:
            # Fetch the file as a stream
            response = cos.get_object(Bucket=bucket_name, Key=file_key)
            # Read the content into a DataFrame
            df = pd.read_csv(BytesIO(response['Body'].read()), **kwargs)
            return df
        except Exception as e:
            print(f"Error reading {file_key} from bucket {bucket_name}: {e}")
            return None
    elif api_type == 'local':
        return pd.read_csv(data_root / file_key, **kwargs)
    
def read_json(file_key):
    if api_type == 'ibm':
        """Read a json file directly from IBM COS into a dict."""
        try:
            # Fetch the file as a stream
            response = cos.get_object(Bucket=bucket_name, Key=file_key)
            # Read the content into a dict
            data = json.load(BytesIO(response['Body'].read()))
            return data
        except Exception as e:
            print(f"Error reading {file_key} from bucket {bucket_name}: {e}")
            return None
    elif api_type == 'local':
        with open(data_root / file_key, "r") as f:
            data = json.load(f)
        return data
    
def file_exists(file_key):
    if api_type == 'ibm':
        """Check if a file exists in the bucket."""
        try:
            cos.head_object(Bucket=bucket_name, Key=file_key)
            return True
        except cos.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            else:
                raise
    elif api_type == 'local':
        return (data_root / file_key).exists()