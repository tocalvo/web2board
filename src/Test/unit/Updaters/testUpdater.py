import json
import os
import unittest

import shutil
from flexmock import flexmock

from libs.PathsManager import TEST_RES_PATH, TEST_SETTINGS_PATH
from libs.Updaters.Updater import Updater, VersionInfo
from libs import utils

versionTestData = {
    "version": "9.9.9",
    "file2DownloadUrl": "file2DownloadUrl",
    "librariesNames": ["l1"]
}


class TestUpdater(unittest.TestCase):
    ORIGINAL_DOWNLOAD_ZIP_PATH = os.path.join(TEST_SETTINGS_PATH, "Updater", "000.zip")
    COPY_DOWNLOAD_ZIP_PATH = os.path.join(TEST_SETTINGS_PATH, "Updater", "copy_000.zip")

    def setUp(self):
        self.updater = Updater()
        self.updater.currentVersionInfoPath = os.path.join(TEST_SETTINGS_PATH, "Updater", "currentVersion.version")
        self.updater.onlineVersionUrl = "onlineVersionUrl"
        self.updater.destinationPath = os.path.join(TEST_SETTINGS_PATH, "Updater", "destinationPath")

        self.originalGetDataFromUrl = utils.getDataFromUrl
        self.originalDownloadFile = utils.downloadFile
        self.originalExtractZip = utils.extractZip

        self.zipToClearPath = None

    def tearDown(self):
        utils.getDataFromUrl = self.originalGetDataFromUrl
        utils.downloadFile = self.originalDownloadFile
        utils.extractZip = self.originalExtractZip

        for libraryName in versionTestData["librariesNames"]:
            if os.path.exists(self.updater.destinationPath + os.sep + libraryName):
                shutil.rmtree(self.updater.destinationPath + os.sep + libraryName)
        if os.path.exists(self.COPY_DOWNLOAD_ZIP_PATH):
            os.remove(self.COPY_DOWNLOAD_ZIP_PATH)

        if os.path.exists(self.updater.destinationPath):
            shutil.rmtree(self.updater.destinationPath)

    def __getMockForGetDataFromUrl(self, returnValue=json.dumps(versionTestData)):
        return flexmock(utils).should_receive("getDataFromUrl").and_return(returnValue)

    def __getMockForDownloadFile(self):
        shutil.copy2(self.ORIGINAL_DOWNLOAD_ZIP_PATH, self.COPY_DOWNLOAD_ZIP_PATH)
        return flexmock(utils).should_receive("downloadFile").and_return(self.COPY_DOWNLOAD_ZIP_PATH)

    def __getMockForExtractZip(self):
        return flexmock(utils).should_receive("extractZip")

    def test_readCurrentVersionInfo_setsCurrentVersionInfoValues(self):
        self.updater.readCurrentVersionInfo()

        self.assertEqual(self.updater.currentVersionInfo.version, "0.0.0")
        self.assertTrue(len(self.updater.currentVersionInfo.librariesNames) >= 1)

    def test_readCurrentVersionInfo_raisesExceptionIfFileNotFound(self):
        self.updater.currentVersionInfoPath = "nonExistingPath"

        with self.assertRaises(IOError):
            self.updater.readCurrentVersionInfo()

    def test_downloadOnlineVersionInfo_setsOnlineVersionInfoValues(self):
        self.__getMockForGetDataFromUrl().once()

        self.updater.downloadOnlineVersionInfo()

        self.assertEqual(self.updater.onlineVersionInfo.version, "9.9.9")
        self.assertEqual(self.updater.onlineVersionInfo.librariesNames, ["l1"])

    def test_isNecessaryToUpdate_raiseExceptionIfCurrentVersionIsNone(self):
        self.updater.onlineVersionInfo = VersionInfo(**versionTestData)

        with self.assertRaises(Exception):
            self.updater.isNecessaryToUpdate()

    def test_isNecessaryToUpdate_raiseExceptionIfOnlineVersionIsNone(self):
        self.updater.currentVersionInfo = VersionInfo(**versionTestData)

        with self.assertRaises(Exception):
            self.updater.isNecessaryToUpdate()

    def test_isNecessaryToUpdate_ReloadsVersionsIfFlagIsTrue(self):
        self.__getMockForGetDataFromUrl()
        self.updater.isNecessaryToUpdate(reloadVersions=True)

        self.assertIsNotNone(self.updater.onlineVersionInfo)
        self.assertIsNotNone(self.updater.currentVersionInfo)

    def test_isNecessaryToUpdate_returnsTrueIfVersionsAreDifferent(self):
        self.updater.currentVersionInfo = VersionInfo(**versionTestData)
        self.updater.onlineVersionInfo = VersionInfo(**versionTestData)
        self.updater.currentVersionInfo.version = "0.1.1"

        self.assertTrue(self.updater.isNecessaryToUpdate())

    def test_isNecessaryToUpdate_raisesExceptionIfDestinationPathDoesNotExist(self):
        self.updater.currentVersionInfo = VersionInfo(**versionTestData)
        self.updater.onlineVersionInfo = VersionInfo(**versionTestData)
        if os.path.exists(self.updater.destinationPath):
            shutil.rmtree(self.updater.destinationPath)

        self.assertRaises(Exception, self.updater.isNecessaryToUpdate)

    def test_isNecessaryToUpdate_returnsTrueIfVersionsAreEqualButNoLibrariesInDestinationPath(self):
        self.updater.currentVersionInfo = VersionInfo(**versionTestData)
        self.updater.onlineVersionInfo = VersionInfo(**versionTestData)
        os.makedirs(self.updater.destinationPath)

        self.assertTrue(self.updater.isNecessaryToUpdate())

    def test_isNecessaryToUpdate_returnsTrueIfVersionsAreEqualAndLibrariesInDestinationPath(self):
        self.updater.currentVersionInfo = VersionInfo(**versionTestData)
        self.updater.onlineVersionInfo = VersionInfo(**versionTestData)
        for libraryName in versionTestData["librariesNames"]:
            if not os.path.exists(self.updater.destinationPath + os.sep + libraryName):
                os.makedirs(self.updater.destinationPath + os.sep + libraryName)

        self.assertFalse(self.updater.isNecessaryToUpdate())

    def test_update_raiseExceptionIfOnlineVersionIsNone(self):
        self.updater.currentVersionInfo = VersionInfo(**versionTestData)
        self.__getMockForDownloadFile().never()
        self.__getMockForExtractZip().never()

        with self.assertRaises(Exception):
            self.updater.update()

    def test_update_ReloadsVersionIfFlagIsTrue(self):
        self.__getMockForGetDataFromUrl()
        self.__getMockForDownloadFile().once()
        self.__getMockForExtractZip().once()

        self.updater.update(reloadVersions=True)

        self.assertIsNotNone(self.updater.onlineVersionInfo)
        self.assertIsNotNone(self.updater.currentVersionInfo)

    def test_update_MoveExtractedFolderToDestinationFolder(self):
        try:
            self.__getMockForGetDataFromUrl()
            self.__getMockForDownloadFile().once()

            self.updater.update(reloadVersions=True)

            self.assertTrue(len(os.listdir(self.updater.destinationPath)) > 0)
        finally:
            if os.path.exists(self.updater.destinationPath):
                shutil.rmtree(self.updater.destinationPath)