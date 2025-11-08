#######################################################################################################################
#
#
#  	Project     	: 	Generic Data generator.
#
#   File            :   utils.py
#
#   Description     :   Generic utility routines
#
#   Created     	:   06 Aug 2025
#                   :   24 Aug 2025 - Refactored so that each data product can go to an individual 
#                   :   defined persistent/DB target. removed DEST, added TARGETS as a , seperated list
#
#                       https://towardsdatascience.com/fake-almost-everything-with-faker-a88429c500f1/
#                       https://fakerjs.dev/guide/localization
#
#   Functions       :   getConfigs
#                   :   mylogger
#                   :   echo_config
#                   :   convert_yymmdd_to_date
#                   :   convert_date_to_yymmdd
#                   :   generate_birth_date
#                   :   pp_json
#                   :   load_jsondata
#
#
########################################################################################################################
__author__      = "Generic Data playground"
__email__       = "georgelza@gmail.com"
__version__     = "0.2"
__copyright__   = "Copyright 2025, - George Leonard"


import json
import random, os, logging
from datetime import datetime


def getConfigs():
    
    config_params = {}
    # General
    config_params["ECHOCONFIG"]             = int(os.environ["ECHOCONFIG"])
    config_params["ECHORECORDS"]            = int(os.environ["ECHORECORDS"])

    config_params["CONSOLE_DEBUGLEVEL"]     = int(os.environ["CONSOLE_DEBUGLEVEL"])
    config_params["FILE_DEBUGLEVEL"]        = int(os.environ["FILE_DEBUGLEVEL"])

    config_params["SOURCEDIR"]              = os.environ["SOURCEDIR"]    
    
    config_params["LOGDIR"]                 = os.environ["LOGDIR"]    
    config_params["LOGGINGFILE"]            = os.path.join(os.environ["LOGDIR"], str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + ".log")

    config_params["VECTOR_STORE"]           = os.environ["VECTOR_STORE"]  # or redis    
    config_params["EMBEDDING_DIM"]          = int(os.environ["EMBEDDING_DIM"])
    
    config_params["TARGETS"]                = [int(x) for x in os.environ["TARGETS"].split(",")]    
    if 1 in config_params["TARGETS"]:
        config_params["MONGO_HOST"]                 = os.environ["MONGO_HOST"]
        config_params["MONGO_PORT"]                 = os.environ["MONGO_PORT"]
        config_params["MONGO_DIRECT"]               = os.environ["MONGO_DIRECT"]
        config_params["MONGO_ROOT"]                 = os.environ["MONGO_ROOT"]
        config_params["MONGO_USERNAME"]             = os.environ["MONGO_USERNAME"]
        config_params["MONGO_PASSWORD"]             = os.environ["MONGO_PASSWORD"]
        config_params["MONGO_DATASTORE"]            = os.environ["MONGO_DATASTORE"]
        config_params["MONGO_COLLECTION"]           = os.environ["MONGO_COLLECTION"]
    
    if 3 in config_params["TARGETS"]: 
        config_params["REDIS_HOST"]                 = os.environ["REDIS_HOST"]
        config_params["REDIS_PORT"]                 = int(os.environ["REDIS_PORT"])
        config_params["REDIS_DB"]                   = int(os.environ["REDIS_DB"])
        config_params["REDIS_PASSWORD"]             = os.environ["REDIS_PASSWORD"]
        config_params["REDIS_INDEX_NAME"]           = os.environ["REDIS_INDEX_NAME"]
        config_params["REDIS_DOC_PREFIX"]           = os.environ["REDIS_DOC_PREFIX"]

        if int(os.environ["REDIS_SSL"]) == 0: 
            config_params["REDIS_SSL"] = False 
        else: 
            print(config_params["REDIS_SSL"])
            config_params["REDIS_SSL"] = True
            config_params["REDIS_SSL_CERT"]         = os.environ["REDIS_SSL_CERT"]
            config_params["REDIS_SSL_KEY"]          = os.environ["REDIS_SSL_KEY"] 
            config_params["REDIS_SSL_CA"]           = os.environ["REDIS_SSL_CA"]

    #end if
    
    return config_params
#end getConfig


def mylogger(filename, console_level, file_level):

    """
    Common Generic mylogger setup, used by master loop for console and file logging.
    """
    
    logger = logging.getLogger(__name__)
    
    # Set the overall logger level to the lowest of the two handlers
    lowest_level = min(console_level, file_level)
    logger.setLevel(lowest_level)


    # create console handler
    ch = logging.StreamHandler()
    
    # Set console log level 
    if console_level == 10:
        ch.setLevel(logging.DEBUG)
        
    elif console_level == 20:
        ch.setLevel(logging.INFO)
        
    elif console_level == 30:
        ch.setLevel(logging.WARNING)
        
    elif console_level == 40:
        ch.setLevel(logging.ERROR)
      
    elif console_level == 50:
        ch.setLevel(logging.CRITICAL)
        
    else:   # == 0 aka logging.NOTSET
        ch.setLevel(logging.INFO)  # Default log level if undefined
        
    # Create a formatter
    ch_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(processName)s - %(message)s')

    ch.setFormatter(ch_formatter)
    logger.addHandler(ch)


    # create file handler
    fh = logging.FileHandler(filename)

   # Set file log level 
    if console_level == 10:
        fh.setLevel(logging.DEBUG)
        
    elif console_level == 20:
        fh.setLevel(logging.INFO)
        
    elif console_level == 30:
        fh.setLevel(logging.WARNING)
        
    elif console_level == 40:
        fh.setLevel(logging.ERROR)
      
    elif console_level == 50:
        fh.setLevel(logging.CRITICAL)
        
    else:   # == 0 aka logging.NOTSET
        fh.setLevel(logging.INFO)  # Default log level if undefined
        
    # Create a formatter
    fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)
    
    return logger
# end mylogger


def echo_config(config_params, mylogger):
    
    if config_params["ECHOCONFIG"] == 1:
        
        mylogger.info("***********************************************************")
        mylogger.info("* ")
        mylogger.info("*          Python ....")
        mylogger.info("* ")
        mylogger.info("***********************************************************")
        mylogger.info("* General")
        mylogger.info("* ")
        mylogger.info("* Console Debuglevel               : " + str(config_params["CONSOLE_DEBUGLEVEL"])) 
        mylogger.info("* File Debuglevel                  : " + str(config_params["FILE_DEBUGLEVEL"]))
        mylogger.info("* ")
        
        mylogger.info("* ")        
        mylogger.info("* Log Directory                    : " + config_params["LOGDIR"])        
        mylogger.info("* Log File                         : " + config_params["LOGGINGFILE"])

        mylogger.info("* ")
        mylogger.info("* Embedding Dimensions             : " + str(config_params["EMBEDDING_DIM"])) 
        mylogger.info("* DB Targets Specified             : " + str(config_params["TARGETS"]))
        mylogger.info("* ")
    
        if 1 in config_params["TARGETS"]:  
            mylogger.info("* ")
            mylogger.info("* Target                           : MogoDB")
            mylogger.info("* Mongo Root                       : " + config_params["MONGO_ROOT"])
            mylogger.info("* Mongo host                       : " + config_params["MONGO_HOST"])
            mylogger.info("* Mongo Port                       : " + str(config_params["MONGO_PORT"]))
            mylogger.info("* Mongo Direct                     : " + config_params["MONGO_DIRECT"])
            mylogger.info("* Mongo Datastore                  : " + config_params["MONGO_DATASTORE"])
            

        if 3 in config_params["TARGETS"]: 
            mylogger.info("* ")
            mylogger.info("* Target                           : Redis")
            mylogger.info("* Redis Host                       : " + config_params["REDIS_HOST"])
            mylogger.info("* Redis Port                       : " + str(config_params["REDIS_PORT"]))
            mylogger.info("* Redis DB                         : " + str(config_params["REDIS_DB"])) 
            mylogger.info("* Redis Index Name                 : " + config_params["REDIS_INDEX_NAME"])
            mylogger.info("* Redis Doc Prefix                 : " + config_params["REDIS_DOC_PREFIX"])

            mylogger.info("* Redis SSL                        : " + str(config_params["REDIS_SSL"]))
            if int(os.environ["REDIS_SSL"]) != 0:             
                mylogger.info("* Redis SSL Cert                   : " + config_params["REDIS_SSL_CERT"])
                mylogger.info("* Redis SSL Key                    : " + config_params["REDIS_SSL_KEY"])
                mylogger.info("* Redis SSL CA                     : " + config_params["REDIS_SSL_CA"])
 
        mylogger.info("* ")
        mylogger.info("***********************************************************")     
        mylogger.info("")
                
# end echo_config



def pp_json(json_thing, sort=True, indents=4):
    
    """
        Pretty Printer to JSON
    """
    
    if type(json_thing) is str:
        print(json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents))
        
    else:
        print(json.dumps(json_thing, sort_keys=sort, indent=indents))

    #end if
    return None
# end pp_json
