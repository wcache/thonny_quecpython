from logging import getLogger
from .fw import FwDownloadHandler

logger = getLogger(__name__)


def download_firmware_api(firmware_file_path, comport):
    logger.info('enter download_firmware_api function. args: {}'.format((firmware_file_path,)))
    fw_download_handler = FwDownloadHandler(firmware_file_path, comport)
    for progress in fw_download_handler.download():
        yield progress
