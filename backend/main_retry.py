from hanlp_restful import HanLPClient
import logging
import wikipedia

HANLP_URL = "https://hanlp.hankcs.com/api"
HANLP_API_KEY = "ODM5M0BiYnMuaGFubHAuY29tOlNMTHZkcjhHM01NenRQN1Q="

HanLP_Client = None

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    if HanLP_Client:
        HanLP_Client = HanLPClient(HANLP_URL,auth = HANLP_API_KEY,language='zh')
        logger.info("HanLP client initialized")
    else:
        logger.error("API not exists")
except Exception as e:
    logger.error(f"Failed initializing : {e}",exc_info=True)
    HanLP_Client = None

try:
    wikipedia.set_lang("zh")
    logger.info("Wikipedia language set to Chinese")
except wikipedia.exceptions.PageError as e:
    logger.warning(f"Failed set language to chinese : {e}",exc_info=True)
    try:
        wikipedia.set_lang("en")
        logger.info("set language to English")
    except wikipedia.exceptions.PageError as e:
        logger.error(f"Failed set language to english : {e}",exc_info=True)
