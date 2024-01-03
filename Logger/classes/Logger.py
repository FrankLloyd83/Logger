import os
from datetime import datetime
import glob
import re
import requests
from requests.exceptions import ConnectionError
import threading
import time


class Logger:
    def __init__(self, path: str):
        self.path = path
        self.checkPath()
        self.patternNameFile = r"^log-(\d{8}).txt$"
        self.url = "https://olaps-logger.azurewebsites.net"

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
    def __init__(self, path: str):
        super().__init__(path)

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
        headers = {"Content-Type": "application/json"}
        data = self.formatMessage(messages)
        try:
            response = requests.post(self.url, data=data, headers=headers)
        except ConnectionError as e:
            raise e

        if response.status_code == 200:
            return response
        else:
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
        connection_successful = self.checkConnectionToServer()
        if not connection_successful:
            self.logToClient(messages)
            self.createThread()
        else:
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
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(self.url, data=buffer_content, headers=headers)
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
        try:
            response = requests.get(self.url)
        except ConnectionError as e:
            return False
        if response.status_code == 200:
            return True

    def createThread(self):
        thread = threading.Thread(target=self.emptyBuffer, args=(self.getLogs(),))
        thread.start()

