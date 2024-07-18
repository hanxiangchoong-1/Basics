import torch
from transformers import pipeline
from tqdm import tqdm

class EmbeddingModel:
    def __init__(self, model_name):
        if torch.backends.mps.is_available():
            self.device = "mps"
            print("Using MPS")
        else:
            self.device = "cpu"
            print("Using CPU")
        ''' 
        Initialize embedding model and pipeline. 
        Load into mac GPU (Change to cuda if using nvidia)
        '''
        self.embedding_pipeline = pipeline("feature-extraction", 
                                            model=model_name, 
                                            trust_remote_code=True, 
                                            device=self.device)
        
    def get_embeddings(self, texts):
        ''' 
        Given a list of strings, return a list of embeddings 
        (List of floating point numbers)
        '''
        embeddings = self.embedding_pipeline(texts, 
                                            truncation=True, 
                                            padding=True, 
                                            max_length=512)
        return embeddings

    def embed_documents(self, documents, text_field="chunk", batch_size=32):
        ''' 
        Given a list of document objects, grab the text, 
        batch embed, then put the embeddings into the document objects.
        '''
        for i in tqdm(range(0, len(documents), batch_size), desc="Embedding documents"):
            batch = documents[i:i+batch_size]
            texts = [doc[text_field] for doc in batch]
            embeddings = self.get_embeddings(texts)
            for doc, embedding in zip(batch, embeddings):
                doc['embedding'] = embedding[0][0]
        return documents