import logging
import os

from libs import utils
from libs.Downloader import Downloader

log = logging.getLogger(__name__)


class VersionInfo:
    def __init__(self, version, file_to_download_url="", libraries_names=list()):
        self.version = version
        """:type : str """
        self.file_to_download_url = file_to_download_url
        """:type : str | dict """
        self.libraries_names = libraries_names
        try:
            self.__get_version_numbers()
        except (ValueError, AttributeError):
            raise Exception("bad format version: {}".format(version))

    def __eq__(self, other):
        return self.version == other.version

    def __ne__(self, other):
        return self.version != other.version

    def __gt__(self, other):
        zipped = zip(self.__get_version_numbers(), other.__get_version_numbers())
        for s, o in zipped:
            if s > o:
                return True
            if s < o:
                return False
        return False

    def __ge__(self, other):
        return self > other or self == other

    def __le__(self, other):
        return other >= self

    def __lt__(self, other):
        return other > self

    def __get_version_numbers(self):
        return [int(n) for n in self.version.split(".")]

    def get_dictionary(self):
        return self.__dict__


class Updater:
    NONE_VERSION = "0.0.0"

    def __init__(self):
        self.current_version_info = None
        """:type : VersionInfo """

        self.onlineVersionUrl = None
        """:type : str """

        self.name = "Updater"
        self.downloader = Downloader()

    @property
    def destination_path(self):
        return None

    def _are_we_missing_libraries(self):
        # todo: this is only for librariesUpdater
        log.debug("[{0}] Checking library names".format(self.name))
        if not os.path.exists(self.destination_path):
            return True
        libraries = utils.list_directories_in_path(self.destination_path)
        libraries = map(lambda x: x.lower(), libraries)
        for cLibrary in self.current_version_info.libraries_names:
            if cLibrary.lower() not in libraries:
                return True

        return len(self.current_version_info.libraries_names) > len(libraries)

    def _update_current_version_to(self, version_to_upload):
        """
        :type version_to_upload: VersionInfo
        """
        log.debug("[{0}] Updating version to: {1}".format(self.name, version_to_upload.version))
        self.current_version_info.version = version_to_upload.version
        self.current_version_info.file_to_download_url = version_to_upload.file_to_download_url
        self.current_version_info.libraries_names = utils.list_directories_in_path(self.destination_path)
        log.info("Current version updated")

    def get_version_number(self, version_info=None):
        """
        :type version_info: VersionInfo
        """
        version_info = self.current_version_info if version_info is None else version_info
        return int(version_info.version.replace('.', ''))

    def is_necessary_to_update(self, version_to_compare=None):
        """
        :type version_to_compare: VersionInfo
        """
        version_to_compare = self.current_version_info if version_to_compare is None else version_to_compare
        log_args = self.name, self.current_version_info.version, version_to_compare.version
        log.debug("[{0}] Checking version {1} - {2}".format(*log_args))
        return self.current_version_info != version_to_compare or self._are_we_missing_libraries()