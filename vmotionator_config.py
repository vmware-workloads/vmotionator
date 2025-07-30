import configparser
import hashlib

from typing import List

DEFAULT_VMOTION_INTERVAL_MIN_SECONDS = 900      # 15 minutes
DEFAULT_VMOTION_INTERVAL_MAX_SECONDS = 1200     # 20 minutes
DEFAULT_VMOTION_VM_COUNT = 1                    # number of VM to vmotion
DEFAULT_VMOTION_VM_EXCLUSIONS = """
vCLS
SupervisorControlPlaneVM
vSAN File Service Node
"""
DEFAULT_VCENTER_PORT = 443
DEFAULT_VCENTER_SSL_VERIFY = True
DEFAULT_SERVICE_LOGFILE = "/var/log/vmotionator/service.log"
DEFAULT_SERVICE_LOG_LEVEL = "DEBUG"
DEFAULT_SERVICE_CONSOLE_LEVEL = "WARNING"
DEFAULT_SERVICE_LOGFILE_MAXSIZE_BYTES = 20 * 1024 * 1024
DEFAULT_SERVICE_LOGFILE_COUNT = 10
DEFAULT_VMOTION_LOGFILE = "/var/log/vmotionator/vmotion.log"
DEFAULT_VMOTION_LOGFILE_MAXSIZE_BYTES = 20 * 1024 * 1024
DEFAULT_VMOTION_LOGFILE_COUNT = 10


class VMotionatorConfig(object):
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)

        #
        # Default Section
        #
        self.vmotion_interval_min_seconds = self.config.getint(section="DEFAULT",
                                                               option="vmotion_interval_min_seconds",
                                                               fallback=DEFAULT_VMOTION_INTERVAL_MIN_SECONDS)

        self.vmotion_interval_max_seconds = self.config.getint(section="DEFAULT",
                                                               option="vmotion_interval_max_seconds",
                                                               fallback=DEFAULT_VMOTION_INTERVAL_MAX_SECONDS)

        self.vmotion_vm_count = self.config.getint(section="DEFAULT",
                                                   option="vmotion_vm_count",
                                                   fallback=DEFAULT_VMOTION_VM_COUNT)

        raw_list = self.config.get(section="DEFAULT",
                                   option="vmotion_vm_exclusions",
                                   fallback=DEFAULT_VMOTION_VM_EXCLUSIONS)
        self.vmotion_vm_exclusions = [item.strip() for item in raw_list.strip().splitlines() if item.strip()]

        #
        # vCenter Server
        #
        self.vcenter_server = self.config.get(section="SERVER",
                                              option="vcenter_server")

        self.vcenter_username = self.config.get(section="SERVER",
                                                option="vcenter_username")

        self.vcenter_password = self.config.get(section="SERVER",
                                                option="vcenter_password")

        self.vcenter_port = self.config.getint(section="SERVER",
                                               option="vcenter_port",
                                               fallback=DEFAULT_VCENTER_PORT)

        self.vcenter_ssl_verify = self.config.getboolean(section="SERVER",
                                                         option="vcenter_ssl_verify",
                                                         fallback=DEFAULT_VCENTER_SSL_VERIFY)

        #
        # Logging Section
        #
        self.service_logfile = self.config.get(section="LOGGING",
                                               option="service_logfile",
                                               fallback=DEFAULT_SERVICE_LOGFILE)

        self.service_logfile_level = self.config.get(section="LOGGING",
                                                     option="service_logfile_level",
                                                     fallback=DEFAULT_SERVICE_LOG_LEVEL)

        self.service_console_level = self.config.get(section="LOGGING",
                                                     option="service_console_level",
                                                     fallback=DEFAULT_SERVICE_CONSOLE_LEVEL)

        self.service_logfile_maxsize_bytes = self.config.getint(section="LOGGING",
                                                                option="service_logfile_maxsize_bytes",
                                                                fallback=DEFAULT_SERVICE_LOGFILE_MAXSIZE_BYTES)

        self.service_logfile_count = self.config.getint(section="LOGGING",
                                                        option="service_logfile_count",
                                                        fallback=DEFAULT_SERVICE_LOGFILE_COUNT)

        self.vmotion_logfile = self.config.get(section="LOGGING",
                                               option="vmotion_logfile",
                                               fallback=DEFAULT_VMOTION_LOGFILE)

        self.vmotion_logfile_maxsize_bytes = self.config.getint(section="LOGGING",
                                                                option="vmotion_logfile_maxsize_bytes",
                                                                fallback=DEFAULT_VMOTION_LOGFILE_MAXSIZE_BYTES)

        self.vmotion_logfile_count = self.config.getint(section="LOGGING",
                                                        option="vmotion_logfile_count",
                                                        fallback=DEFAULT_VMOTION_LOGFILE_COUNT)

    def json(self, hash_password=True):
        return {
            "config_file": self.config_file,
            "vmotion_interval_min_seconds": self.vmotion_interval_min_seconds,
            "vmotion_interval_max_seconds": self.vmotion_interval_max_seconds,
            "vmotion_vm_count": self.vmotion_vm_count,
            "vcenter_server": self.vcenter_server,
            "vcenter_username": self.vcenter_username,
            "vcenter_password": self.hash(self.vcenter_password) if hash_password else self.vcenter_password,
            "vcenter_port": self.vcenter_port,
            "vcenter_ssl_verify": self.vcenter_ssl_verify,
            "service_logfile": self.service_logfile,
            "service_logfile_level": self.service_logfile_level,
            "service_console_level": self.service_console_level,
            "service_logfile_maxsize_bytes": self.service_logfile_maxsize_bytes,
            "service_logfile_count": self.service_logfile_count,
            "vmotion_logfile": self.vmotion_logfile,
            "vmotion_logfile_maxsize_bytes": self.vmotion_logfile_maxsize_bytes,
            "vmotion_logfile_count": self.vmotion_logfile_count,
        }

    def print(self):
        for k, v in self.json().items():
            print(f"{k}: '{v}'")

    @classmethod
    def hash(cls, data: str) -> str:
       return hashlib.sha256(bytes(data, "utf-8")).hexdigest()

    @property
    def vmotion_interval_min_seconds(self) -> int:
        return self._vmotion_interval_min_seconds

    @vmotion_interval_min_seconds.setter
    def vmotion_interval_min_seconds(self, vmotion_interval_min_seconds: int):
        if not isinstance(vmotion_interval_min_seconds, int):
            raise ValueError(f"vmotion_interval_min_seconds must be an int (input: '{vmotion_interval_min_seconds}')")
        if vmotion_interval_min_seconds < 1:
            raise ValueError(f"vmotion_interval_min_seconds must be greater than 0 (input: {vmotion_interval_min_seconds})")
        self._vmotion_interval_min_seconds = vmotion_interval_min_seconds

    @property
    def vmotion_interval_max_seconds(self) -> int:
        return self._vmotion_interval_max_seconds

    @vmotion_interval_max_seconds.setter
    def vmotion_interval_max_seconds(self, vmotion_interval_max_seconds: int):
        if not isinstance(vmotion_interval_max_seconds, int):
            raise ValueError(f"vmotion_interval_max_seconds must be an int (input: '{vmotion_interval_max_seconds}')")
        if vmotion_interval_max_seconds < 1:
            raise ValueError(f"vmotion_interval_max_seconds must be greater than 0 (input: {vmotion_interval_max_seconds})")
        self._vmotion_interval_max_seconds = vmotion_interval_max_seconds

    @property
    def vmotion_vm_count(self) -> int:
        return self._vmotion_vm_count

    @vmotion_vm_count.setter
    def vmotion_vm_count(self, vmotion_vm_count: int):
        if not isinstance(vmotion_vm_count, int):
            raise ValueError(f"vmotion_vm_count must be an int (input: '{vmotion_vm_count}')")
        if vmotion_vm_count < 1:
            raise ValueError(f"vmotion_vm_count must be greater than 0 (input: {vmotion_vm_count})")
        self._vmotion_vm_count = vmotion_vm_count

    @property
    def vmotion_vm_exclusions(self) -> List[str]:
        return self._vmotion_vm_exclusions

    @vmotion_vm_exclusions.setter
    def vmotion_vm_exclusions(self, vmotion_vm_exclusions: List[str]):
        if not isinstance(vmotion_vm_exclusions, list):
            raise ValueError(f"vmotion_vm_exclusions must be a list (input: '{vmotion_vm_exclusions}')")
        if not all(isinstance(x, str) for x in vmotion_vm_exclusions):
            raise ValueError(f"vmotion_vm_exclusions must be a list of strings (input: '{vmotion_vm_exclusions}')")
        self._vmotion_vm_exclusions = vmotion_vm_exclusions

    @property
    def vcenter_server(self) -> str:
        return self._vcenter_server

    @vcenter_server.setter
    def vcenter_server(self, vcenter_server: str):
        if not isinstance(vcenter_server, str):
            raise ValueError(f"vcenter_server must be a string (input: '{vcenter_server}')")
        self._vcenter_server = vcenter_server

    @property
    def vcenter_username(self) -> str:
        return self._vcenter_username

    @vcenter_username.setter
    def vcenter_username(self, vcenter_username: str):
        if not isinstance(vcenter_username, str):
            raise ValueError(f"vcenter_username must be a string (input: '{vcenter_username}')")
        self._vcenter_username = vcenter_username

    @property
    def vcenter_password(self) -> str:
        return self._vcenter_password

    @property
    def vcenter_password_hashed(self) -> str:
        return self.hash(self._vcenter_password)

    @vcenter_password.setter
    def vcenter_password(self, vcenter_password: str):
        if not isinstance(vcenter_password, str):
            raise ValueError(f"vcenter_password must be a string (input: '{vcenter_password}')")
        self._vcenter_password = vcenter_password

    @property
    def vcenter_port(self) -> int:
        return self._vcenter_port

    @vcenter_port.setter
    def vcenter_port(self, vcenter_port: int):
        if vcenter_port < 1 or vcenter_port > 65535:
            raise ValueError(f"vcenter_port must be in [1, 63535] (was {vcenter_port}).")
        self._vcenter_port = vcenter_port

    @property
    def vcenter_ssl_verify(self) -> bool:
        return self._vcenter_ssl_verify

    @vcenter_ssl_verify.setter
    def vcenter_ssl_verify(self, vcenter_ssl_verify: str):
        if not isinstance(vcenter_ssl_verify, bool):
            raise ValueError(f"vcenter_ssl_verify must be a boolean (input: '{vcenter_ssl_verify}')")
        self._vcenter_ssl_verify = vcenter_ssl_verify

    @property
    def service_logfile(self) -> str:
        return self._service_logfile

    @service_logfile.setter
    def service_logfile(self, service_logfile: str):
        if not isinstance(service_logfile, str) and len(service_logfile) < 1:
            raise ValueError(f"service_logfile must be a string with at least 1 character (input: '{service_logfile}')")
        self._service_logfile = service_logfile

    @property
    def service_logfile_level(self) -> str:
        return self._service_logfile_level

    @service_logfile_level.setter
    def service_logfile_level(self, service_logfile_level: str):
        if not isinstance(service_logfile_level, str):
            raise ValueError(f"service_logfile_level must be a string (input: '{service_logfile_level}')")
        self._service_logfile_level = service_logfile_level

    @property
    def service_console_level(self) -> str:
        return self._service_console_level

    @service_console_level.setter
    def service_console_level(self, service_console_level: str):
        if not isinstance(service_console_level, str):
            raise ValueError(f"service_console_level must be a string (input: '{service_console_level}')")
        self._service_console_level = service_console_level

    @property
    def service_logfile_maxsize_bytes(self) -> int:
        return self._service_logfile_maxsize_bytes

    @service_logfile_maxsize_bytes.setter
    def service_logfile_maxsize_bytes(self, service_logfile_maxsize_bytes: int):
        if service_logfile_maxsize_bytes < 1:
            raise ValueError(
                f"service_logfile_maxsize_bytes must be greater than 1024 (was {service_logfile_maxsize_bytes}).")
        self._service_logfile_maxsize_bytes = service_logfile_maxsize_bytes

    @property
    def service_logfile_count(self) -> int:
        return self._service_logfile_count

    @service_logfile_count.setter
    def service_logfile_count(self, service_logfile_count: int):
        if service_logfile_count < 2:
            raise ValueError(f"service_logfile_count must be greater than 1 (was {service_logfile_count}).")
        self._service_logfile_count = service_logfile_count

    @property
    def vmotion_logfile(self) -> str:
        return self._vmotion_logfile

    @vmotion_logfile.setter
    def vmotion_logfile(self, vmotion_logfile: str):
        if not isinstance(vmotion_logfile, str) and len(vmotion_logfile) < 1:
            raise ValueError(f"service_logfile must be a string with at least 1 character (input: '{vmotion_logfile}')")
        self._vmotion_logfile = vmotion_logfile

    @property
    def vmotion_logfile_maxsize_bytes(self) -> int:
        return self._vmotion_logfile_maxsize_bytes

    @vmotion_logfile_maxsize_bytes.setter
    def vmotion_logfile_maxsize_bytes(self, vmotion_logfile_maxsize_bytes: int):
        if vmotion_logfile_maxsize_bytes < 1:
            raise ValueError(
                f"vmotion_logfile_maxsize_bytes must be greater than 1024 (was {vmotion_logfile_maxsize_bytes}).")
        self._vmotion_logfile_maxsize_bytes = vmotion_logfile_maxsize_bytes

    @property
    def vmotion_logfile_count(self) -> int:
        return self._vmotion_logfile_count

    @vmotion_logfile_count.setter
    def vmotion_logfile_count(self, vmotion_logfile_count: int):
        if vmotion_logfile_count < 2:
            raise ValueError(f"vmotion_logfile_count must be greater than 1 (was {vmotion_logfile_count}).")
        self._vmotion_logfile_count = vmotion_logfile_count