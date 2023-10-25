import time
import os
import pprint
import requests
import json
import logging
import shutil
from datetime import datetime
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logConsoleHandler = logging.StreamHandler()

if not os.path.exists("logs"):
    os.mkdir("logs")

logFileHandler = logging.FileHandler(
    f"logs/{datetime.now().strftime('%Y-%m-%d_%H-%m-%S')}.log")


class WebDataHandler:
    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        logger.info("Created web rolnik handler")
        self.listDict = dict()
        self.unixTimestamp = time.mktime(datetime.now().timetuple())

    class InvalidResponseCode(Exception):
        """Response code is not 200"""
        pass

    class WrongPathProvided(Exception):
        """Provided path does not exist"""
        pass

    def get_unix_timestamp(self, timestamp: datetime = datetime.now()):
        self.unixTimestamp = time.mktime(timestamp.timetuple())
        return self.unixTimestamp

    def get_list(self, category = 'gabinety', parse_to_dict: bool = True, to_file: bool = True,
                 filename: os.path = os.path.join("files", "list.json")):

        unix_timestamp = time.mktime(datetime.now().timetuple())
        response = requests.get(f"https://rolniknysa.pl/plan/biezacy/dane/lista.json?nocache={unix_timestamp}")
        logger.info(f"Request -> {response.status_code}")
        logger.debug(f"  Size: {response.headers.get('content-length', 0)} bytes")

        if to_file:
            if os.path.exists(filename):
                os.remove(filename)

            with open(filename, 'x') as file:
                logger.info(f"Writing list to {filename}")
                file.write(response.text)
                file.close()
                logger.debug(f"Closed {filename}")

        if parse_to_dict:
            list_dict = dict()
            for entry in response.json()[category]:
                list_dict[entry['nazwa']] = entry['plik']
            self.listDict = list_dict
            return list_dict
        else:
            return response.json()

    def get_file(self, filename, to_object: bool = False):
        response = requests.get(f"https://rolniknysa.pl/plan/biezacy/dane/{filename}.json", stream=True)

        if response.status_code == 200:
            size = int(response.headers.get('content-length', 0))
            block_size = 10
            response_content = response.text
            progress_bar = tqdm(total=size, unit='B', unit_scale=True)

            if os.path.exists(os.path.join("files", f"{filename}.json")):
                os.remove(os.path.join("files", f"{filename}.json"))

            open(os.path.join("files", f"{filename}.json"), 'x').close()
            with open(os.path.join("files", f"{filename}.json"), 'wb') as file:
                content = b''
                for block in response.iter_content(block_size):
                    file.write(block)
                    progress_bar.update(len(block))
                file.close()

            if to_object:
                exec(f"self.{filename} = file_json")
            return {
                "json": response_content,
                "var_name": filename
            }
        else:
            raise self.InvalidResponseCode

    # def get_all_files(self, to_object: bool = False):
    #     list_respone = requests.get()

    def parse_json(self, filename: str):
        if not filename:
            raise self.WrongPathProvided
        output_path = os.path.join("result", f"{filename}.out.json")
        if os.path.exists(output_path):
            logger.warn(f"{output_path} already exists. Removing...")
            os.remove(output_path)

        open(output_path, 'x').close()
        with open(output_path, 'w') as out_file:
            with open(os.path.join("files", f"{filename}.json"), 'r'):
                # TODO
                pass
        return output_path


web_handler = WebDataHandler()

web_handler.get_list()

if os.path.exists("files"):
    shutil.rmtree("files")
os.mkdir("files")

for elem in web_handler.listDict:
    logger.info(f"Downloading {str(elem)} file")
    logger.debug(web_handler.get_file(web_handler.listDict[elem])["var_name"])

if os.path.exists("result"):
    shutil.rmtree("result")
os.mkdir("result")


