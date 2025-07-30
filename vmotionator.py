#! /usr/bin/env python3
import argparse
import logging
import logging.handlers
from configparser import NoOptionError

from pathlib import Path

from utils import create_folders, get_logging_level
from vmotionator_config import VMotionatorConfig
from vmotionator_service import VMotionatorService


def create_logger(logger_name: str,
                  logfile: str,
                  log_level: int,
                  console_level: int,
                  logfile_maxsize_bytes: int,
                  logfile_count: int) -> logging.Logger:

    logger = logging.getLogger(logger_name)

    # Set logging level
    logger.setLevel(log_level)

    # Set log format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)

    # Create file handler
    file_handler = logging.handlers.RotatingFileHandler(logfile,
                                                        maxBytes=logfile_maxsize_bytes,
                                                        backupCount=logfile_count)
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def main():

    # Get CLI input
    parser = argparse.ArgumentParser(prog='vmotionator', description='Random vMotion Service for Linux')
    parser.add_argument('-c', '--config', type=str, required=True)
    args = parser.parse_args()
    config_file = args.config

    # Check if a configuration file exists
    if not (Path(config_file).is_file() and Path(config_file).exists()):
        print(f"Configuration file is missing: '{config_file}'")
        parser.print_help()
        exit(1)

    # Parse configuration file
    try:
        config = VMotionatorConfig(config_file=config_file)
        config.print()
    except NoOptionError as e:
        print(f"Error: Configuration file '{config_file}': {e}")
        exit(1)

    # Create required folders
    create_folders(config.service_logfile)
    create_folders(config.vmotion_logfile)

    # Create logger
    logger = create_logger(logger_name='',
                           logfile=config.service_logfile,
                           log_level=get_logging_level(config.service_logfile_level),
                           console_level=get_logging_level(config.service_console_level),
                           logfile_maxsize_bytes=config.service_logfile_maxsize_bytes,
                           logfile_count=config.service_logfile_count)

    logger_vmotion = create_logger(logger_name='vmotion',
                                   logfile=config.vmotion_logfile,
                                   log_level=get_logging_level("DEBUG"),
                                   console_level=get_logging_level("WARNING"),
                                   logfile_maxsize_bytes=config.vmotion_logfile_maxsize_bytes,
                                   logfile_count=config.vmotion_logfile_count)
    logger_vmotion.propagate = False


    logger.debug("Starting vMotionator service")
    logger.debug(f"Config: {config.json()}")
    logger.debug(f"Minimum wait time: {config.vmotion_interval_min_seconds}")
    logger.debug(f"Maximum wait time: {config.vmotion_interval_max_seconds}")
    logger.debug(f"Number of VM(s) to migrate per interval: {config.vmotion_vm_count}")
    logger_vmotion.debug("Starting vMotionator service")

    obj = VMotionatorService(vmotion_interval_min_seconds=config.vmotion_interval_min_seconds,
                             vmotion_interval_max_seconds=config.vmotion_interval_max_seconds,
                             vmotion_vm_count=config.vmotion_vm_count,
                             vmotion_vm_exclusions=config.vmotion_vm_exclusions,
                             vcenter_server=config.vcenter_server,
                             vcenter_username=config.vcenter_username,
                             vcenter_password=config.vcenter_password,
                             vcenter_port=config.vcenter_port,
                             vcenter_ssl_verify=config.vcenter_ssl_verify)
    obj.run()


if __name__ == "__main__":
    main()

