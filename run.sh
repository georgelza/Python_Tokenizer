#!/bin/bash

. ./.pws

export ECHOCONFIG=1                             # Print to screen our current values as per this file, might make sense to have this as it goes into the log files.
export ECHORECORDS=0                            # If you want to see everything fly by, this will slow things down!!!

export CONSOLE_DEBUGLEVEL=20                    # Console Handler
export FILE_DEBUGLEVEL=20                       # File Handler
# logging.CRITICAL: 50
# logging.ERROR: 40
# logging.WARNING: 30
# logging.INFO: 20
# logging.DEBUG: 10
# logging.NOTSET: 0

export SOURCEDIR=source

export LOGDIR=logs

export VECTOR_STORE=redis                       # or redis

export TARGETS=3
# 0 no DB send
# 1 MongoDB
# 3 Redis

export EMBEDDING_DIM=384

# MongoDB
export MONGO_ROOT=mongodb
export MONGO_USERNAME=
# export MONGO_PASSWORD=
export MONGO_HOST=localhost
export MONGO_PORT=27017
export MONGO_DIRECT=directConnection=true 
export MONGO_DATASTORE=vector_store
export MONGO_COLLECTION=embeddings

# REDIS - see .pws
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_INDEX_NAME=doc_embeddings
export REDIS_DOC_PREFIX=doc:
export REDIS_SSL=0
# export REDIS_PASSWORD=
# export REDIS_SSL_CERT=
# export REDIS_SSL_KEY=
# export REDIS_SSL_CA=


python3 app/main.py
