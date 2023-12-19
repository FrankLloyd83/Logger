import os
from datetime import datetime
import glob
import re


class Logger:
    def __init__(self, path):
        self.path = path
        self.checkPath()
        self.patternNameFile = r"^log-(\d{8}).txt$"

    def checkPath(self) -> None:
        """
        Checks if the specified path exists and creates it if it doesn't.

        Raises:
            NotADirectoryError: If the specified path is a file instead of a directory.
        """

        if os.path.splitext(self.path)[1]:
            raise NotADirectoryError(self.path)

        # Vérifier si le dossier existe
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

        # Obtenez la date actuelle
        date_actuelle = datetime.now()

        # Formatez la date en nombres
        fileLogName = "log-" + self.getDateToString(date_actuelle) + ".txt"

        path = os.path.join(self.path, fileLogName)

        # Normalize the path
        normalized_path = os.path.normpath(path)

        return normalized_path

    def formatMessage(self, messages) -> str:
        """
        Formats the given messages into a single string with a timestamp.

        Args:
            messages (list): A list of messages to be formatted.

        Returns:
            str: The formatted message string with a timestamp.
        """
        s = ";".join(messages)
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

    def check_file_name(self, file_name, start_date, end_date) -> bool:
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

    def log(self, *messages) -> None:
        """
        Writes the log messages to the log file.

        Parameters:
        * messages: Variable number of messages to be logged.

        Returns:
        None
        """
        logFile = self.selectLogFileFromCurrDate()
        try:
            # Ouvrez le fichier en mode d'ajout/lecture
            with open(logFile, "a+") as file:
                # Effectuez les opérations d'écriture ici
                file.write(self.formatMessage(messages))
        except FileNotFoundError:
            # Si le fichier n'existe pas, créez-le et réessayez
            with open(logFile, "w") as file:
                file.write(self.formatMessage(messages))
