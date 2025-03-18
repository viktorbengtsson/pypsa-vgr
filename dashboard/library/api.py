import os
import sys
from pathlib import Path
import json
import pandas as pd
from io import BytesIO
from pathlib import Path
import streamlit as st

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

# Check environment variables for API type

api_type = os.getenv("API", "local")

# Local or Streamlit cloud data root

def set_data_root():
    if "DATA_ROOT" in st.secrets:
        # Manually set in Community Cloud Secrets
        return st.secrets["DATA_ROOT"]
    else:
        from paths import api_path
        return api_path

# AWS configuration

if api_type == 'aws':
    import boto3
    s3 = boto3.client("s3", region_name="eu-central-1")  # Frankfurt region
    bucket_name = 'generation-toolkit-vgr-api-prod'
elif api_type == 'aws-local':
    from boto3 import Session
    session = Session(profile_name="600627346413_PowerUser_with_billing")
    s3 = session.client("s3", region_name="eu-central-1")  # Frankfurt region
    bucket_name = 'generation-toolkit-vgr-api-prod'
elif api_type == 'local':
    data_root = set_data_root()

# Utility functions

def read_csv(file_key, **kwargs):
    if api_type == 'aws':
        """Read a CSV file directly from AWS S3 into a pandas DataFrame."""
        try:
            # Fetch the file as a stream
            response = s3.get_object(Bucket=bucket_name, Key=file_key)
            # Read the content into a DataFrame
            df = pd.read_csv(BytesIO(response['Body'].read()), **kwargs)
            return df
        except Exception as e:
            print(f"Error reading {file_key} from bucket {bucket_name}: {e}")
            return None
    elif api_type == 'local':
        return pd.read_csv(data_root / file_key, **kwargs)
    
def read_json(file_key):
    if api_type == 'aws':
        """Read a JSON file directly from AWS S3 into a dict."""
        try:
            # Fetch the file as a stream
            response = s3.get_object(Bucket=bucket_name, Key=file_key)
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
    if api_type == 'aws':
        """Check if a file exists in the bucket."""
        try:
            s3.head_object(Bucket=bucket_name, Key=file_key)
            return True
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            else:
                raise
    elif api_type == 'local':
        return (data_root / file_key).exists()