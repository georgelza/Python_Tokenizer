#######################################################################################################################
#
#
#  	Project     	: 	Vectorizer
#
#   File            :   connections.py
#
#   Description     :   Generic utility routines
#
#   Created     	:   20 Oct 2025 - 
#
#   Functions       :   
#                   :   MongoVectorStore
#                   :   RedisVectorStore
#
########################################################################################################################
__author__      = "Generic Data playground"
__email__       = "georgelza@gmail.com"
__version__     = "0.2"
__copyright__   = "Copyright 2025, - George Leonard"


import json, sys
import logging
import numpy as np
from typing import List, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod

try:
    import pymongo
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
    print("MongoDB, Module Import Successful")
    
except ImportError as err:
    print("MongoDB, Module Import Error {err}")
    sys.exit(1)
 
try:
    from redis.commands.search.query import Query
    from redis.commands.search.field import VectorField, TextField, NumericField, TagField
    from redis.commands.search.index_definition import IndexDefinition, IndexType
    import redis
    print("Redis,   Module Import Successful")
    
except ImportError as err:
    print("Redis,   Module Import Error {err}")
    sys.exit(1)
       

class DatabaseConnectionError(Exception):
    
    """Custom exception for database connection errors"""
    
    pass
#end DatabaseConnectionError


class DatabaseOperationError(Exception):
    
    """Custom exception for database operation errors"""
    
    pass
#end DatabaseOperationError

class VectorStore(ABC):
    """Abstract base class for vector stores"""
    
    def __init__(self, config_params: Dict[str, Any], mylogger: logging.Logger):
        self.config_params  = config_params
        self.mylogger       = mylogger
        self.connection     = None
        self._is_connected  = False
    #end __init__
    
    
    @property
    def is_connected(self) -> bool:
        
        """Check if database is connected"""
        
        return self._is_connected
    #end is_connected
    
    
    # @abstractmethod
    # def _build_uri(self) -> str:
    #     """Build MongoDB connection URI"""
    #     pass
    # #end _build_uri
       
    
    @abstractmethod
    def store_embeddings(self, chunks: List[Dict], embeddings: np.ndarray, 
                        document_name: str) -> List[str]:
        """Store embeddings in the vector store"""
        pass
    #end store_embeddings
    
    
    @abstractmethod
    def similarity_search(self, query_embedding: np.ndarray, top_k: int = 5,
                         file_type_filter: str = None) -> List[Dict]:
        """Search for similar documents"""
        pass
    #end similarity_search
    
    
    @abstractmethod
    def get_statistics(self) -> Dict:
        """Get statistics about stored documents"""
        pass
    #end get_statistics
    
    
    @abstractmethod
    def close(self):
        """Close connections"""
        pass
    #end close
#end VectorStore


class MongoVectorStore(VectorStore):
    """MongoDB implementation of vector store"""
    
    def __init__(self, 
                 config_params: Dict[str, Any], 
                 mylogger:      logging.Logger):
                
        super().__init__(config_params, mylogger)
        self.client         = None
        self.database       = None
        self.collection     = {}
        self.embedding_dim  = self.config_params["EMBEDDING_DIM"]

        try:
            self.client         = MongoClient(self._build_uri())

            self.db             = self.client[self.config_params["MONGO_DATASTORE"]]
            self.collection     = self.db[self.config_params["MONGO_COLLECTION"]]
            self._is_connected  = True
            
            self.mylogger.info('✓ MongoDB vector store initialized: {host} {dbstore}'.format(
                host        = self.config_params["MONGO_HOST"],
                dbstore     = self.config_params["MONGO_DATASTORE"],
                collection  = self.config_params["MONGO_COLLECTION"]
            ))           
        
        except pymongo.errors.ServerSelectionTimeoutError as err:
            self.mylogger.error('MongoDB connection failed: {host} {dbstore} {err}'.format(
                host        = self.config_params["MONGO_HOST"],
                dbstore     = self.config_params["MONGO_DATASTORE"],
                err         = err
            ))
            raise DatabaseConnectionError(f"MongoDB connection failed: {err}")
            
        except ConnectionFailure as err:
            self.mylogger.error('MongoDB connection failed: {host} {dbstore} {err}'.format(
                host        = self.config_params["MONGO_HOST"],
                dbstore     = self.config_params["MONGO_DATASTORE"],
                err         = err
            ))
            raise DatabaseConnectionError(f"MongoDB connection failed: {err}")
            
        except Exception as err:
            self.mylogger.error('MongoDB connection error: {host} {dbstore} {err}'.format(
                host     = self.config_params["MONGO_HOST"],
                dbstore  = self.config_params["MONGO_DATASTORE"],
                err      = err
            ))
            raise DatabaseConnectionError(f"MongoDB connection error: {err}")
        
        #end try
    #end __init__
    

    def _build_uri(self) -> str:
    
        """Build MongoDB connection URI"""
        root        = self.config_params["MONGO_ROOT"]
        host        = self.config_params["MONGO_HOST"]
        port        = int(self.config_params["MONGO_PORT"])
        username    = self.config_params.get("MONGO_USERNAME", "")
        password    = self.config_params.get("MONGO_PASSWORD", "")
        direct      = self.config_params.get("MONGO_DIRECT", "")
        
        if root == "mongodb":
            if username:
                uri = f'{root}://{username}:{password}@{host}:{port}/?{direct}'
                
            else:
                uri = f'{root}://{host}:{port}/?{direct}'
                
        else:  # mongodb+srv
            if username:
                uri = f'{root}://{username}:{password}@{host}'
                
            else:
                uri = f'{root}://{host}'
        
        return uri
    #end _build_mongo_uri
    
    
    def store_embeddings(self, chunks: List[Dict], embeddings: np.ndarray,
                        document_name: str) -> List[str]:
        documents = []
                
        for chunk, embedding in zip(chunks, embeddings):
            doc = {
                'document_name':    document_name,
                'text':             chunk['text'],
                'page_number':      chunk['page_number'],
                'chunk_index':      chunk['chunk_index'],
                'source':           chunk['source'],
                'file_type':        chunk['file_type'],
                'embedding':        embedding.tolist(),
                'embedding_model':  'all-MiniLM-L6-v2',
                'embedding_dimension': len(embedding),
                'created_at':       datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f%f")
            }
            pp_json = json.dumps(doc, indent=4)
            print(pp_json)
            
            documents.append(doc)
        
        result = self.collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    #end store_embeddings
    
    
    def similarity_search(self, query_embedding: np.ndarray, top_k: int = 5,
                         file_type_filter: str = None) -> List[Dict]:
        filter_query = {}
        if file_type_filter:
            filter_query['file_type'] = file_type_filter
        
        all_docs = list(self.collection.find(filter_query))
        
        if not all_docs:
            return []
        
        results = []
        for doc in all_docs:
            doc_embedding = np.array(doc['embedding'])
            
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )
            
            results.append({
                'text':             doc['text'],
                'document_name':    doc['document_name'],
                'page_number':      doc.get('page_number'),
                'file_type':        doc['file_type'],
                'similarity_score': float(similarity),
                'id':               str(doc['_id'])
            })
        
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:top_k]
    #end similarity_search
    
    
    def get_statistics(self) -> Dict:
        total_docs = self.collection.count_documents({})
        
        stats = {
            'total_chunks': total_docs,
            'by_file_type': {}
        }
        
        for file_type in ['pdf', 'txt', 'docx']:
            count = self.collection.count_documents({'file_type': file_type})
            if count > 0:
                stats['by_file_type'][file_type] = count
        
        return stats
    # get_statistics
    
    
    def close(self):
        self.client.close()
    #end close
#end MongoVectorStore


# https://redis.io/docs/latest/develop/clients/redis-py/queryjson/
class RedisVectorStore(VectorStore):
    """Redis implementation of vector store with RedisSearch"""
    
    def __init__(self, 
                 config_params: Dict[str, Any], 
                 mylogger:      logging.Logger):
        
        super().__init__(config_params, mylogger)
        self.client         = None
        self.embedding_dim  = self.config_params["EMBEDDING_DIM"]
        self.index_name     = config_params['REDIS_INDEX_NAME']
        self.prefix         = config_params['REDIS_DOC_PREFIX']
        
        try:
            self.client = redis.Redis(
                host             = config_params["REDIS_HOST"], 
                port             = config_params['REDIS_PORT'], 
                db               = config_params['REDIS_DB'], 
                decode_responses = False
            )
            
            self.client.ping()
            self._is_connected  = True
            
            #Create index if it doesn't exist
            self._create_index()
            
            self.mylogger.info('✓ Redis vector store initialized: {host}:{port}/{db}'.format(
                host = self.config_params["REDIS_HOST"],
                port = self.config_params.get("REDIS_PORT", 6379), 
                db   = self.config_params.get("REDIS_DB",   0)
            ))            
            
        except redis.exceptions.ConnectionError as err:
            self.mylogger.error('Redis connection failed: {host}:{port} {err}'.format(
                host = self.config_params["REDIS_HOST"],
                port = self.config_params["REDIS_PORT"],
                err  = err
            ))
            raise DatabaseConnectionError(f"Redis connection failed: {err}")
        
        except Exception as err:
            self.mylogger.error('Redis connection failed: {host}:{port} {err}'.format(
                host = self.config_params["REDIS_HOST"],
                port = self.config_params["REDIS_PORT"],
                err  = err
            ))
        #end try
    #end __init__
    
    
    def _create_index(self):
        """Create Redis search index with vector field"""
                
        try:
            index = self.client.ft(self.index_name)
            index.info()
            
            # Check if index exists
            self.client.ft(self.index_name).info()
            self.mylogger.error('  Index already exists')

        except:
            
            # Create new index
            schema = (
                TextField("document_name"),
                TextField("text"),
                NumericField("page_number"),
                NumericField("chunk_index"),
                TextField("source"),
                TagField("file_type"),
                TextField("embedding_model"),
                NumericField("embedding_dimension"),
                TextField("created_at"),
                VectorField("embedding",
                    "FLAT", {
                        "TYPE": "FLOAT32",
                        "DIM": self.embedding_dim,
                        "DISTANCE_METRIC": "COSINE"
                    }
                )
            )
            
            definition = IndexDefinition(
                prefix     = [self.prefix],
                index_type = IndexType.HASH
            )
            
            self.client.ft(self.index_name).create_index(
                schema,
                definition=definition
            )
            self.mylogger.info('✓  Created new search index')

        #end try
    #enf _create_index
    
    
    def store_embeddings(self, 
                         chunks:        List[Dict], 
                         embeddings:    np.ndarray,
                         document_name: str
                        ) -> List[str]:
        doc_ids = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Generate unique key
            doc_id = f"{self.prefix}{document_name}:{chunk['chunk_index']}:{i}"
            doc_ids.append(doc_id)
            
            # Prepare document data
            doc_data = {
                'document_name':    document_name,
                'text':             chunk['text'],
                'page_number':      chunk['page_number'] if chunk['page_number'] else -1,
                'chunk_index':      chunk['chunk_index'],
                'source':           chunk['source'],
                'file_type':        chunk['file_type'],
                'embedding_model':  'all-MiniLM-L6-v2',
                'embedding_dimension': len(embedding),
                'created_at':       datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                'embedding':        embedding.astype(np.float32).tobytes()
            }
            
            # Store in Redis
            self.client.hset(doc_id, mapping=doc_data)
        
        return doc_ids
    #end store_embeddings
    
    
    def similarity_search(self, 
                          query_embedding: np.ndarray, 
                          top_k: int = 5,
                          file_type_filter: str = None
                          ) -> List[Dict]:

        # Prepare query
        query_vector = query_embedding.astype(np.float32).tobytes()
        
        # Build filter and query string
        if file_type_filter:
            base_query = f"(@file_type:{{{file_type_filter}}})"
            
        else:
            base_query = "*"
        
        #end if
        
        # Create KNN query - proper syntax
        query_str = f"{base_query}=>[KNN {top_k} @embedding $vec AS score]"
        
        q = Query(query_str).return_fields(
            "document_name", 
            "text", 
            "page_number", 
            "file_type", 
            "score"
        ).sort_by("score").paging(0, top_k).dialect(2)
        
        try:
            results = self.client.ft(self.index_name).search(
                q,
                query_params={"vec": query_vector}
            )
            
            output = []
            for doc in results.docs:
                page_num = int(doc.page_number) if int(doc.page_number) != -1 else None
                
                output.append({
                    'text':             doc.text,
                    'document_name':    doc.document_name,
                    'page_number':      page_num,
                    'file_type':        doc.file_type,
                    'similarity_score': 1 - float(doc.score),  # Convert distance to similarity
                    'id':               doc.id
                })
            #end for
            return output
        except Exception as e:
            self.mylogger.error('Search error: {err}'.format(
                err = e
            ))
            return []
        #end try
    #end similarity_search
    
    
    def get_statistics(self) -> Dict:
        try:
            info = self.client.ft(self.index_name).info()
            total_docs = int(info['num_docs'])
            
            stats = {
                'total_chunks': total_docs,
                'by_file_type': {}
            }
            
            # Count by file type
            for file_type in ['pdf', 'txt', 'docx']:
                q       = Query(f"@file_type:{{{file_type}}}").no_content()
                results = self.client.ft(self.index_name).search(q)
                if results.total > 0:
                    stats['by_file_type'][file_type] = results.total
            
                #end if
            #end for
            return stats
        except Exception as e:
            self.mylogger.error('Statistics error: {err}'.format(
                err = e
            ))
            return {'total_chunks': 0, 'by_file_type': {}}
        #end try
    #end get_statistics


    def close(self):
        self.client.close()
    #end close
#end RedisVectorStore