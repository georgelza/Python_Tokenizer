#######################################################################################################################
#
#
#  	Project     	: 	Read text, pdf or docx file and tokenize content, storing into MongoDB or REDIS, currently
#
#   File            :   main.py
#
#   Description     :   Multi-Format Document Vectorization with Redis or MongoDB Storage
#
#   Created     	:   20 Oct 2025
#                   :   
#                   :   Supports: PDF, TXT, DOCX (Word Documents)
#                   :   Vector Stores: Redis (with RedisSearch) or MongoDB
#
#
#   Functions       :   DocumentVectorizer
#                   :   get_documents_from_path
#                   :   __main__
#
#
########################################################################################################################
__author__      = "Generic Data playground"
__email__       = "georgelza@gmail.com"
__version__     = "0.1"
__copyright__   = "Copyright 2025, - George Leonard"
   

import PyPDF2, docx
import os, json, sys
import logging
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

from utils import *
from connections import *


class DocumentVectorizer:
    
    """Main document vectorizer with pluggable vector stores"""
    
    def __init__(self, 
                 config_params: Dict[str, Any], 
                 mylogger: logging.Logger
                 ):

        self.config_params  = config_params
        self.mylogger       = mylogger
        self.connection     = None
        self._is_connected  = False
        self.client         = None
        self.vectorizer     = None
        
        """
        Initialize Document Vectorizer
        
        Args:
            config_params:  Configuration parameters
            mylogger:       Logger instance
        """

        try:            
            # Initialize embedding model        
            self.mylogger.info('Loading embedding model...')

            self.model              = SentenceTransformer('all-MiniLM-L6-v2')
            vector_store_type       = self.config_params["VECTOR_STORE"]
            self.vector_store_type  = vector_store_type

            # Initialize vector store
            if vector_store_type.lower() == "mongodb":
                self.client = MongoVectorStore(config_params, mylogger)
                
            elif vector_store_type.lower() == "redis":
                self.client = RedisVectorStore(config_params, mylogger)

            else:
                raise ValueError(f"Unsupported vector store: {vector_store_type}. Use 'mongodb' or 'redis'")
            
            #end if
            
            self.mylogger.info('✓ Using {vector_store_type} as vector store'.format(
               vector_store_type = vector_store_type.upper()
            ))
        
        except Exception as e:
            self.mylogger.error(f"Error initializing DocumentVectorizer: {str(e)}")
        #end try
    #end __init__
    
        
    # We've completed creating the VctorStore connection and initialization methods.
    # Now, we will implement methods for extracting text from different document formats.
    
    
    def extract_text_from_pdf(self, 
                              file_path: str
                              ) -> List[Dict[str, any]]:
        
        chunks = []
        with open(file_path, 'rb') as file:
            
            self.mylogger.info("File Opened: {file_path}".format( 
                file_path = file_path
            ))
            
            pdf_reader  = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page        = pdf_reader.pages[page_num]
                text        = page.extract_text()
                paragraphs  = text.split('\n\n')
                
                for para_num, paragraph in enumerate(paragraphs):
                    if paragraph.strip():
                        chunks.append({
                            'text':         paragraph.strip(),
                            'page_number':  page_num + 1,
                            'chunk_index':  para_num,
                            'source':       file_path,
                            'file_type':    'pdf'
                        })
        return chunks
    #end extract_text_from_pdf
    
    
    def extract_text_from_txt(self, 
                              file_path: str
                              ) -> List[Dict[str, any]]:
        
        chunks = []
        with open(file_path, 'r', encoding='utf-8') as file:
            
            self.mylogger.info("File Opened: {file_path}".format( 
                file_path = file_path
            ))
            
            content = file.read()
            
            paragraphs = content.split('\n\n')
            
            for para_num, paragraph in enumerate(paragraphs):
                if paragraph.strip():
                    chunks.append({
                        'text':         paragraph.strip(),
                        'page_number':  None,
                        'chunk_index':  para_num,
                        'source':       file_path,
                        'file_type':    'txt'
                    })
        return chunks
    #end extract_text_from_txt
    
    
    def extract_text_from_docx(self, 
                               file_path: str
                               ) -> List[Dict[str, any]]:
        
        chunks = []
        doc = docx.Document(file_path)
        
        self.mylogger.info("File Opened: {file_path}".format( 
            file_path = file_path
        ))
        
        for para_num, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text.strip()
            if text:
                chunks.append({
                    'text':         text,
                    'page_number':  None,
                    'chunk_index':  para_num,
                    'source':       file_path,
                    'file_type':    'docx'
                })
        return chunks
    #end extract_text_from_docx
    
    
    def extract_text(self, 
                     file_path: str
                     ) -> List[Dict[str, any]]:
        
        _, extension = os.path.splitext(file_path)
        extension    = extension.lower()
        
        if extension == '.pdf':
            
            self.mylogger.info("Processing PDF file: {file_path}".format(
                file_path = file_path
            ))    
            return self.extract_text_from_pdf(file_path)
        
        elif extension == '.txt':
            self.mylogger.info("Processing TXT file: {file_path}".format(
                file_path = file_path
            ))
            return self.extract_text_from_txt(file_path)
        
        elif extension in ['.docx', '.doc']:
            if extension == '.doc':
                self.mylogger.error("Warning: .doc format detected. Only .docx is fully supported.")
                
            self.mylogger.info("Processing DOCX file: {file_path}".format(
                file_path = file_path
            ))
            return self.extract_text_from_docx(file_path)
        
        else:
            raise ValueError(f"Unsupported file type: {extension}")
    #end extract_text
    
    
    def generate_embeddings(self, 
                            texts: List[str]
                            ) -> np.ndarray:
        
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        return embeddings
    #end generate_embeddings
    
    
    def process_document(self, 
                         file_path:     str, 
                         document_name: str = None
                         ) -> Dict:
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if document_name is None:
            document_name = os.path.basename(file_path)
        
        print(f"\n{'='*60}")
        print(f"Processing Document: {file_path}")
        print(f"{'='*60}")
        
        # Extract text
        self.mylogger.info("Extracting text from document...")
        chunks = self.extract_text(file_path)
        self.mylogger.debug("✓ Extracted {len} text chunks".format(
            len = len(chunks)
        ))
        
        if not chunks:
            raise ValueError("No text content found in document")
        
        # Generate embeddings
        self.mylogger.info("Generating embeddings...")
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.generate_embeddings(texts)
        self.mylogger.info("✓ Generated embeddings with dimension {embeddings}".format(
            embeddings = embeddings.shape[1]
        ))
        
        # Store in vector store
        self.mylogger.info("✓ Storing in {vector_store_type}...".format(
            vector_store_type = self.vector_store_type
        ))
        
        doc_ids = self.client.store_embeddings(chunks, embeddings, document_name)
        
        self.mylogger.info("✓ Successfully stored {doc_ids} chunks".format(
            doc_ids = len(doc_ids)
        ))
        
        return {
            'document_name':        document_name,
            'file_type':            chunks[0]['file_type'],
            'total_chunks':         len(chunks),
            'inserted_ids':         doc_ids[:3],  # Show first 3 IDs
            'embedding_dimension':  embeddings.shape[1],
            'vector_store':         self.vector_store_type
        }
    #end process_document
    
    
    def similarity_search(self, 
                          query:            str, 
                          top_k:            int = 5,
                          file_type_filter: str = None
                         ) -> List[Dict]:
        
        query_embedding = self.model.encode([query])[0]
        
        return self.client.similarity_search(query_embedding, top_k, file_type_filter)
    #end similarity_search
    
    
    def get_statistics(self) -> Dict:
        
        return self.client.get_statistics()
    #end get_statistics
    
    
    def close(self):
        
        self.client.close()
    #end close
#end DocumentVectorizer


def get_documents_from_path(path:       str, 
                            file_types: List[str] = None, 
                            recursive:  bool      = False
                            ) -> List[str]:
    
    """
    Get all document files from a directory path
    
    Args:
        path: Directory path to scan
        file_types: List of file extensions to include (e.g., ['pdf', 'txt', 'docx'])
                   If None, includes all supported types
        recursive: If True, scan subdirectories recursively
        
    Returns:
        List of file paths
    """
    
    # Default to all supported types
    if file_types is None:
        file_types = ['pdf', 'txt', 'docx', 'doc']
    
    # Normalize extensions
    extensions = {f'.{ext.lower().lstrip(".")}' for ext in file_types}
    documents  = []
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path not found: {path}")
    
    if not os.path.isdir(path):
        raise ValueError(f"Path is not a directory: {path}")
    
    if recursive:
        # Walk through all subdirectories
        for root, dirs, files in os.walk(path):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext.lower() in extensions:
                    full_path = os.path.join(root, file)
                    documents.append(full_path)
    else:
        # Only scan the specified directory
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isfile(full_path):
                _, ext = os.path.splitext(item)
                if ext.lower() in extensions:
                    documents.append(full_path)
    
    return sorted(documents)
#end get_documents_from_path


if __name__ == "__main__":
    
    try:
        config_params   = getConfigs()
        logger_instance = mylogger(config_params["LOGGINGFILE"], config_params["CONSOLE_DEBUGLEVEL"], config_params["FILE_DEBUGLEVEL"])
        echo_config(config_params, logger_instance)
               
        vectorizer = DocumentVectorizer(
            config_params,
            logger_instance
        )
                    
        logger_instance.info("✓ Document Vectorizer initialized.")
        
        # Get documents from path with optional filters
        documents_path = os.path.join(os.getcwd(), config_params["SOURCEDIR"])
        documents      = get_documents_from_path(
            documents_path, 
            recursive = False
        )
        # #or 
        # documents = get_documents_from_path(
        #     documents_path, 
        #     file_types = ['pdf', 'txt']
        # )
        # #or
        # documents = get_documents_from_path(
        #     documents_path, 
        #     file_types = ['pdf', 'docx'], 
        #     recursive  = True
        # )
                
        for doc_path in documents:
            
            try:
                result = vectorizer.process_document(doc_path)
                
                print(f"\n✓ Processing Complete!")
                print(f"  Document:     {result['document_name']}")
                print(f"  Type:         {result['file_type']}")
                print(f"  Chunks:       {result['total_chunks']}")
                print(f"  Vector Store: {result['vector_store']}")
                
            except FileNotFoundError:
                print(f"\n✗ File not found: {doc_path}")
                
            except Exception as e:
                print(f"\n✗ Error: {str(e)}")
            #end try
        #end for
        
        
        # Statistics
        print(f"\n{'='*60}")
        print("Database Statistics")
        print(f"{'='*60}")
        
        
        stats = vectorizer.get_statistics()
        print(f"Total chunks: {stats['total_chunks']}")
        if stats['by_file_type']:
            print("By file type:")
            for ftype, count in stats['by_file_type'].items():
                print(f"  {ftype}: {count}")
            #end for
        #end if
        
        
        # Similarity search
        print(f"\n{'='*60}")
        print("Similarity Search")
        print(f"{'='*60}")
        results = vectorizer.similarity_search("machine learning", top_k=3)
        
        for i, doc in enumerate(results, 1):
            print(f"\n[Result {i}]")
            print(f"Score: {doc['similarity_score']:.4f}")
            print(f"Document: {doc['document_name']} ({doc['file_type']})")
            print(f"Text: {doc['text'][:150]}...")
        #end for
        
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt caught! Exiting gracefully.")
        
    finally:
        print("Cleanup operations (if any) can go here.")
        # Cleanup
        vectorizer.close()
    #end try    
#end main