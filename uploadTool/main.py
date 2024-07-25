import os
import sys 
import logging 
import pandas as pd
import uuid
import argparse

from dotenv import load_dotenv
load_dotenv()

# Remove the parent directory from sys.path if you want to clean up
sys.path.pop(0)

''' 
Load files from parent directory (Python Script)
'''
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
from elastic_helpers import ESBulkIndexer, ESQueryMaker
from elastic_config import BASIC_CONFIG
sys.path.pop(0)

# Initialize Elasticsearch
ELASTIC_CLOUD_ID = os.environ.get('ELASTIC_CLOUD_ID')
ELASTIC_USERNAME = os.environ.get('ELASTIC_USERNAME')
ELASTIC_PASSWORD = os.environ.get('ELASTIC_PASSWORD')
ELASTIC_CLOUD_AUTH = (ELASTIC_USERNAME, ELASTIC_PASSWORD)
es_bulk_indexer = ESBulkIndexer(cloud_id=ELASTIC_CLOUD_ID, credentials=ELASTIC_CLOUD_AUTH)
es_query_maker = ESQueryMaker(cloud_id=ELASTIC_CLOUD_ID, credentials=ELASTIC_CLOUD_AUTH)

def generate_unique_id():
    return str(uuid.uuid4())

def main(csv_path, batch_size):
    # Load Data
    csv = pd.read_csv(csv_path)

    csv_dict = csv.to_dict()

    cols = ["uid"] + list(csv_dict.keys())
    count = len(csv_dict[cols[1]])
    docs = []
    for i in range(count):
        unique_id = generate_unique_id()
        obj = dict(zip(cols, [unique_id] + [csv_dict[j][i] for j in cols[1:]]))
        docs += [obj]

    # Upload
    index_name = "blog_authorship"
    index_exists = es_bulk_indexer.check_index_existence(index_name=index_name)
    if not index_exists:
        es_bulk_indexer.create_es_index(es_configuration=BASIC_CONFIG, index_name=index_name)

    success_count = es_bulk_indexer.bulk_upload_documents(
        index_name=index_name, 
        documents=docs, 
        id_col='uid',
        batch_size=batch_size
    )
    
    print(f"Successfully uploaded {success_count} documents.")

if __name__ == "__main__":
    '''
    Sample: python script_name.py /path/to/your/csvfile.csv
    '''
    parser = argparse.ArgumentParser(description="Ingest CSV file and upload to Elastic Cloud")
    parser.add_argument("csv_path", type=str, help="Path to the CSV file to be ingested")
    parser.add_argument("batch_size", type=int, help="Batch size of upload")
    args = parser.parse_args()
    
    main(args.csv_path, args.batch_size)