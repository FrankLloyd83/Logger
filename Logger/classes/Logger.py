import os
from datetime import datetime
import glob
import re
import requests
from requests.exceptions import ConnectionError
import threading
import time
import jwt
import json


class Logger:
    def __init__(self, config: dict):
        self.path = os.getcwd() + "/" + config["LOG_PATH"]
        self.tenant_id = config["TENANT_ID"]
        self.client_id = config["CLIENT_ID"]
        self.client_secret = config["CLIENT_SECRET"]
        self.scope = config["LOG_SCOPE"]
        self.checkPath()
        self.patternNameFile = r"^log-(\d{8}).txt$"
        #self.url = "https://olaps-logger.azurewebsites.net"
        self.url = "http://localhost:8000"
    
    def get_public_key(self, issuer: str, kid: str) -> jwt.algorithms.RSAAlgorithm:
        """
        Retrieves the public key from the authentication server.

        Args:
            issuer (str): The URL of the authentication server.
            kid (str): The key ID of the public key to retrieve.

        Returns:
            RSAAlgorithm: The RSAAlgorithm object representing the retrieved public key.
        """
        jwks_url = issuer + f"/discovery/keys?appid={self.client_id}"
        jwks = requests.get(jwks_url).json()
        for key in jwks["keys"]:
            if key["kid"] == kid:
                return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))

    def validateAccessToken(self, token: str, issuer: str, client_id: str) -> bool:
        """
        Validates the given access token.

        Args:
            token (str): The access token to be validated.
            issuer (str): The issuer of the access token.
            client_id (str): The client ID of the access token.

        Returns:
            bool: True if the access token is valid, False otherwise.
        """
        header, payload, signature = token.split(".")

        header = jwt.get_unverified_header(token)
        kid = header["kid"]
        public_key = self.get_public_key(issuer, kid)

        options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_iss": True,
            "verify_aud": True,
            "require": ["exp", "iss", "aud"],
        }

        try:
            claims = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience="api://{}".format(client_id),
                options=options,
            )
        except jwt.ExpiredSignatureError as e:
            print(e)
            return False
        except jwt.InvalidIssuerError as e:
            print(e)
            return False
        except jwt.InvalidAudienceError as e:
            print(e)
            return False
        except jwt.InvalidTokenError as e:
            print(e)
            return False
        except Exception as e:
            print(e)
            return False
        print("validateAccessToken(): Token validated successfully.")
        return True

    def checkPath(self) -> None:
        """
        Checks if the specified path exists and creates it if it doesn't.

        Raises:
            NotADirectoryError: If the specified path is a file instead of a directory.
        """

        if os.path.splitext(self.path)[1]:
            raise NotADirectoryError(self.path)

        if not os.path.exists(self.path):
            os.makedirs(self.path)
            print(f"Le dossier {self.path} a été créé avec succès.")

    def getDateToString(self, date: datetime.date) -> str:
        """
        Converts a datetime.date object to a string representation in the format 'YYYYMMDD'.

        Args:
            date (datetime.date): The date to be converted.

        Returns:
            str: The string representation of the date in the format 'YYYYMMDD'.
        """
        annee = date.year
        mois = date.month
        jour = date.day

        s = (
            str(annee)
            + ("0" if mois < 10 else "")
            + str(mois)
            + ("0" if jour < 10 else "")
            + str(jour)
        )
        return s

    def selectLogFileFromCurrDate(self) -> str:
        """
        Selects the log file based on the current date.

        Returns:
            str: The normalized path of the log file.
        """
        date_actuelle = datetime.now()
        fileLogName = "log-" + self.getDateToString(date_actuelle) + ".txt"
        path = os.path.join(self.path, fileLogName)
        normalized_path = os.path.normpath(path)

        return normalized_path

    def selectLogFileFromMessageDate(self, message: str) -> str or None:
        """
        Selects the log file based on the timestamp of the log.

        Returns:
            str: The normalized path of the log file.
        """
        timestamp = message.split(";")[0]
        date_stamp = timestamp.split(" ")[0]
        try:
            date_object = datetime.strptime(date_stamp, "%Y-%m-%d")
            date_message = date_object.strftime("%Y%m%d")
            fileLogName = f"log-{date_message}.txt"
            path = os.path.join(self.path, fileLogName)
            normalized_path = os.path.normpath(path)
        except ValueError:
            return None

        return normalized_path

    def formatMessage(self, messages: tuple) -> str:
        """
        Formats the given messages into a single string with a timestamp.

        Args:
            messages (tuple): A tuple of messages to be formatted.

        Returns:
            str: The formatted message string beginning with a timestamp.
        """
        s = str(datetime.now())
        for e in messages:
            s += ";" + str(e)
        s.replace("\n", "\\n")
        s += "\n"
        return s

    def getLogs(
        self,
        dateStart: datetime.date = None,
        dateEnd: datetime.date = None,
        desc: bool = True,
    ) -> list:
        """
        Retrieves logs within a specified date range.

        Args:
            token (str): The access token to be validated.
            dateStart (datetime.date, optional): The start date of the range. Defaults to None.
            dateEnd (datetime.date, optional): The end date of the range. Defaults to None.
            desc (bool, optional): Specifies whether the logs should be sorted in descending order. Defaults to True.

        Returns:
            list: A list of log entries within the specified date range.
        """
        de = None
        ds = None
        if dateEnd == None:
            de = datetime.now()
        else:
            de = dateEnd

        if dateStart == None:
            ds = datetime(1111, 1, 1)
        else:
            ds = dateStart

        listLogfiles = glob.glob(f"{self.path}/*")
        matching_files = [
            file
            for file in listLogfiles
            if self.check_file_name(
                file, self.getDateToString(ds), self.getDateToString(de)
            )
        ]
        sortedMatchedLogFiles = sorted(
            matching_files, key=lambda x: os.path.basename(x), reverse=desc
        )

        logs = []

        for file in sortedMatchedLogFiles:
            with open(file, "r") as f:
                lines = f.readlines()
                for line in lines:
                    logs.append(line.strip())

        return logs

    def check_file_name(self, file_name: str, start_date: str, end_date: str) -> bool:
        """
        Checks if the given file name matches the expected pattern and falls within the specified date range.

        Args:
            file_name (str): The name of the file to be checked.
            start_date (str): The start date of the date range.
            end_date (str): The end date of the date range.

        Returns:
            bool: True if the file name matches the pattern and falls within the date range, False otherwise.
        """
        match = re.match(self.patternNameFile, os.path.basename(file_name))
        if match:
            file_date = str(match.group(1))
            if start_date <= file_date <= end_date:
                return True
        return False


class LoggerServer(Logger):
    def log(self, messages: str) -> None:
        """
        Writes the log messages to the log file.

        Parameters:
        messages: str - The log messages to be written to the log file.

        Returns:
        None
        """
        for message in messages.split("\n"):
            if message != "":
                logFile = self.selectLogFileFromMessageDate(message)
                try:
                    with open(logFile, "a+") as file:
                        file.write(message + "\n")
                except FileNotFoundError:
                    with open(logFile, "w") as file:
                        file.write(message + "\n")


class LoggerClient(Logger):
    def __init__(self, config: dict):
        super().__init__(config)

    def get_logger_token(self, token: str) -> str:
        """
        Retrieves the logger token from the authentication server.

        Args:
            token (str): The access token to be validated.

        Returns:
            str: The logger token.
        """
        try:
            logger_token = requests.post(
                f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": self.scope,
                    "assertion": token,
                    "requested_token_use": "on_behalf_of",
                },
                timeout=30,
            ).json()
            self.token = logger_token["access_token"]
            print("get_logger_token(): Token retrieved successfully.")
        except Exception as e:
            print(e)
            self.token = None

    def logToServer(self, messages: tuple) -> requests.Response or None:
        """
        Sends log messages to a central server.

        Args:
            messages (tuple): tuple of log messages to be sent.

        Returns:
            requests.Response or None: The response object if the request is successful, None otherwise.

        Raises:
            ConnectionError: If the request fails.
        """
        print("logToServer(): Sending log to server.")
        url = f"{self.url}/Send"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}
        data = self.formatMessage(messages)
        try:
            response = requests.post(url, data=data, headers=headers)
        except ConnectionError as e:
            print("logToServer(): Failed to connect to server", e)
            raise e

        if response.status_code == 200:
            print("logToServer(): Log sent successfully. Response status code: ", response.status_code)
            return response
        else:
            print("logToServer(): Failed to send log to server. Response status code:", response.status_code)
            return None

    def logToClient(self, messages: tuple) -> None:
        """
        Logs the given messages to a local file.

        Args:
            messages (tuple): tuple of messages to be logged locally.

        Returns:
            None
        """

        logFile = self.selectLogFileFromCurrDate()
        try:
            with open(logFile, "a+") as file:
                file.write(self.formatMessage(messages))
        except FileNotFoundError:
            with open(logFile, "w") as file:
                file.write(self.formatMessage(messages))

    def log(self, *messages: str) -> None:
        print("log(): Is connection to server successful?")
        connection_successful = self.checkConnectionToServer()
        if not connection_successful:
            print("log(): No.")
            self.logToClient(messages)
            self.createThread()
        else:
            print("log(): Yes.")
            self.logToServer(messages)

    def emptyBuffer(self, buffer: list) -> None:
        """
        Empties the buffer into the log file.

        Args:
            buffer (list): The buffer to be emptied.

        Returns:
            None
        """
        while not self.checkConnectionToServer():
            time.sleep(5)
        buffer_content = "\n".join(buffer)
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}
        url = f"{self.url}/Send"
        try:
            response = requests.post(url, data=buffer_content, headers=headers)
        except ConnectionError as e:
            raise e

        if response.status_code == 200:
            files = glob.glob(f"{self.path}/*")
            for f in files:
                os.remove(f)
        else:
            raise Exception(
                f"Could not empty buffer. Status code: {response.status_code}"
            )

    def checkConnectionToServer(self) -> None:
        print(self.token)
        url = f"{self.url}/checkConnection"
        print(url)
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.get(url, headers=headers, timeout=30)
        except ConnectionError as e:
            print("checkConnectionToServer(): Failed to connect to server", e)
            print("checkConnectionToServer(): Response status code:", response.status_code)
            return False
        except Exception as e:
            print("checkConnectionToServer(): Failed to connect to server", e)
            return False
        if response.status_code == 200:
            return True

    def createThread(self):
        thread = threading.Thread(target=self.emptyBuffer, args=(self.getLogs(),))
        thread.start()
