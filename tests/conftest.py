import logging
import logging.config

# 設定ファイル(logging.conf)の読込
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s [%(module)s, %(lineno)d]")
