import uuid
import re
from llama_index.core import SimpleDirectoryReader

class DocumentProcessor:
    def __init__(self):
        pass 
    
    def load_documents(self, directory_path):
        ''' 
        Load all documents in directory
        '''
        reader = SimpleDirectoryReader(input_dir=directory_path)
        return reader.load_data()

    def chunk_documents(self, documents, chunk_size=256, overlap=32):
        ''' 
        Chunk the text of each document, with overlaps for improved clarity. 
        Assign each chunk with a unique id and an index, and link it back to its parent.
        This will allow us to piece the original document back together if we ever need to. 
        '''
        chunked_documents = []

        for doc in documents:
            # Split the text into words
            words = re.findall(r'\S+', doc['text'])
            
            # Create chunks
            for i in range(0, len(words), chunk_size - overlap):
                chunk_words = words[i:i + chunk_size]
                chunk_text = ' '.join(chunk_words)

                # Create a new document object for this chunk
                chunk_doc = {
                    'id_': str(uuid.uuid4()),  # Generate a new unique ID
                    'chunk': chunk_text,  # Add the new 'chunk' field
                    'chunk_index': len(chunked_documents),  # Add an index for this chunk
                    'parent_id': doc['id_'],  # Add a reference to the parent document
                    'chunk_word_count': len(chunk_words)  # Add word count of the chunk
                }

                # Copy all other fields from the original document
                for key, value in doc.items():
                    if key != 'text' and key not in chunk_doc:
                        chunk_doc[key] = value

                chunked_documents.append(chunk_doc)

        return chunked_documents