import atexit
import hashlib
import logging
import random
import re
import signal
import ssl
import threading

from pyVim.connect import SmartConnect, Disconnect
from pyVim.task import WaitForTask
# noinspection PyUnresolvedReferences
from pyVmomi import vim, vmodl
from threading import Event
from typing import List

from vmotionator_exception import VMotionatorException

logger = logging.getLogger(__name__)
logger_vmotion = logging.getLogger('vmotion')


class VMotionatorService(object):
    def __init__(self,
                 vmotion_interval_min_seconds: int,
                 vmotion_interval_max_seconds: int,
                 vmotion_vm_count: int,
                 vmotion_vm_exclusions: List[str],
                 vcenter_server: str,
                 vcenter_username: str,
                 vcenter_password: str,
                 vcenter_port: int = 443,
                 vcenter_ssl_verify: bool = True,
                 ):
        logger.debug(
            f"__init__: ["
            f"{vmotion_interval_min_seconds},"
            f"{vmotion_interval_max_seconds}, "
            f"{vmotion_vm_count}, "
            f"{vmotion_vm_exclusions}, "
            f"{vcenter_server}, "
            f"{vcenter_username}, "
            f"{self.hash(vcenter_password)}, "
            f"{vcenter_port}, "
            f"{vcenter_ssl_verify}]")

        self.vmotion_interval_min_seconds = vmotion_interval_min_seconds
        self.vmotion_interval_max_seconds = vmotion_interval_max_seconds
        self.vmotion_vm_count = vmotion_vm_count
        self.vmotion_vm_exclusions = vmotion_vm_exclusions
        self.vcenter_server = vcenter_server
        self.vcenter_username = vcenter_username
        self.vcenter_password = vcenter_password
        self.vcenter_port = vcenter_port
        self.vcenter_ssl_verify = vcenter_ssl_verify
        self.__exit = Event()

    @classmethod
    def hash(cls, data: str) -> str:
        return hashlib.sha256(bytes(data, "utf-8")).hexdigest()

    @classmethod
    def filter_templates(cls, vms: List[vim.VirtualMachine]) -> List[vim.VirtualMachine]:
        return [vm for vm in vms if not vm.config.template]

    @classmethod
    def filter_vms(cls, vms: List[vim.VirtualMachine], exclusions: List[str]) -> List[vim.VirtualMachine]:
        # Pre-compile regexes
        regexes = [re.compile(p) for p in exclusions]

        # Filter people whose name matches any pattern
        return [p for p in vms if not any(r.search(p.name) for r in regexes)]

    def _obfuscate_msg(self, msg: str):
        return re.sub(f"{self.vcenter_password}", f"{self.hash(self.vcenter_password)}", msg)

    def _debug(self, msg):
        logger.debug(self._obfuscate_msg(msg))

    def _info(self, msg):
        logger.info(self._obfuscate_msg(msg))

    def _warning(self, msg):
        logger.warning(self._obfuscate_msg(msg))

    def _error(self, msg):
        logger.error(self._obfuscate_msg(msg))

    def _critical(self, msg):
        logger.critical(self._obfuscate_msg(msg))

    @classmethod
    def __host_ready(cls, host: vim.HostSystem) -> bool:
        vmotion = host.configManager.vmotionSystem
        return (host.runtime.connectionState == 'connected'
                and not host.runtime.inMaintenanceMode
                and host.runtime.powerState == 'poweredOn'
                and vmotion
                and vmotion.netConfig)

    @classmethod
    def __get_all_vms(cls, content):
        container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
        return list(container.view)

    @classmethod
    def __get_cluster_for_vm(cls, vm):
        parent = vm.resourcePool.parent
        while parent and not isinstance(parent, vim.ClusterComputeResource):
            parent = parent.parent
        return parent

    @classmethod
    def __get_eligible_hosts(cls, cluster, current_host):
        return [host for host in cluster.host if host != current_host and cls.__host_ready(host)]

    def __perform_vmotion(self, vm, destination_host):
        self._debug(f"__perform_vmotion: {vm.name}' from '{vm.runtime.host.name}' to '{destination_host.name}.")
        logger_vmotion.info(f"'{vm.name}' from '{vm.runtime.host.name}' to '{destination_host.name}'")

        # Relocate VM
        relocate_spec = vim.vm.RelocateSpec(host=destination_host)
        task = vm.Relocate(relocate_spec)
        self.wait_for_task(task)

        # vMotion Complete
        print(f"vMotion complete: {vm.name} moved to {destination_host.name}")
        logger_vmotion.info(f"'{vm.name}' moved to '{destination_host.name}'")

    def wait_for_task(self, task):
        self._debug(f"wait_for_task: waiting for task '{ task.info.key }'")
        try:
            WaitForTask(task)
        except vmodl.fault.RequestCanceled:
            self._warning(f"wait_for_task: task '{task.info.key}' was cancelled")
            return
        self._debug(f"wait_for_task: task '{task.info.key}' completed")

    def perform_vmotion(self):
        self._debug(f"perform_vmotion")

        # Create SSL context
        if self.vcenter_ssl_verify:
            self._debug(f"perform_vmotion: Creating default ssl context")
            context = ssl.create_default_context()
        else:
            self._debug(f"perform_vmotion: Creating an unverified ssl context")
            context = ssl._create_unverified_context()

        # Connect to vCenter
        self._debug(f"perform_vmotion: Connecting to vCenter server ")
        si = SmartConnect(host=self.vcenter_server,
                          user=self.vcenter_username,
                          pwd=self.vcenter_password,
                          port=self.vcenter_port,
                          sslContext=context)

        # Setup cleanup
        atexit.register(Disconnect, si)

        # Get content from vCenter server
        content = si.RetrieveContent()

        # Get VMS from vCenter server
        all_vms = self.__get_all_vms(content)
        if not all_vms:
            self._error("perform_vmotion: No virtual machines found.")
            return
        self._info(f"perform_vmotion: Found {len(all_vms)} virtual machines.")
        self._debug(f"perform_vmotion: All VMS: '{", ".join([vm.name for vm in all_vms])}'")

        # Exclude VM Templates
        vms = self.filter_templates(vms=all_vms)
        self._info(f"perform_vmotion: Excluded {len(all_vms) - len(vms)} templates.")
        self._debug(f"perform_vmotion: VMS: '{", ".join([vm.name for vm in vms])}'")

        # Remove VM exclusions
        included_vms = self.filter_vms(vms=vms, exclusions=self.vmotion_vm_exclusions)
        self._info(f"perform_vmotion: Excluded {len(vms) - len(included_vms)} virtual machines.")
        self._debug(f"perform_vmotion: Included VMS: '{", ".join([vm.name for vm in included_vms])}'")

        # Pick random non-excluded VMs to migrate
        print(f"Picking {self.vmotion_vm_count} VM to vMotion")
        random_vms = random.sample(included_vms, self.vmotion_vm_count)
        print(f"Selected VM(s) {", ".join([random_vm.name for random_vm in random_vms])}")
        self._info(f"perform_vmotion: Selected VM(s): {", ".join([random_vm.name for random_vm in random_vms])}")

        # Create vMotion threads
        threads = []
        for random_vm in random_vms:

            # Find VM cluster
            self._debug(f"perform_vmotion: Migrating VM '{random_vm.name}'")
            cluster = self.__get_cluster_for_vm(random_vm)
            if not cluster:
                self._error(f"perform_vmotion: Cluster not found for VM '{random_vm.name}'")
                return
            self._debug(f"perform_vmotion: Cluster for VM '{random_vm.name}' is '{cluster.name}'")

            # Find target hosts in VM cluster
            self._debug(f"perform_vmotion: Finding eligible hosts in cluster '{cluster.name}'")
            eligible_hosts = self.__get_eligible_hosts(cluster, random_vm.runtime.host)
            if not eligible_hosts:
                self._error(f"perform_vmotion: No eligible hosts found for VM '{random_vm.name}'")
                return
            self._debug(f"perform_vmotion: Eligible hosts: [{", ".join([host.name for host in eligible_hosts])}]")

            # Pick a random target host in the VM cluster
            target_host = random.choice(eligible_hosts)
            self._debug(f"perform_vmotion: Target host for '{random_vm.name}' is '{target_host.name}'")

            # Create and append thread
            self._debug(f"perform_vmotion: Creating thread to vMotion {random_vm.name}' to '{target_host.name}'")
            thread = threading.Thread(target=self.__perform_vmotion, args=(random_vm, target_host, ))
            threads.append(thread)

        # Perform vMotions
        for thread in threads:
            self._debug(f"perform_vmotion: Starting thread '{thread.name}'")
            thread.start()

        # Wait for threads to complete
        self._debug(f"perform_vmotion: Waiting for threads to complete'")
        for thread in threads:
            self._debug(f"perform_vmotion: Waiting on thread '{thread.name}'")
            thread.join(timeout=300)

        # Disconnect
        Disconnect(si)

    # noinspection PyBroadException
    def run(self):

        # Setup signal handlers for SIGTERM, SIGINT and SIGHUP
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGHUP, self.stop)

        # noinspection PyBroadException
        try:
            while not self.__exit.is_set():

                # Select a random wait interval
                # We do this to create some variability in the VM
                # migration intervals.
                self._debug(f"run: selecting random wait time between "
                            f"{self.vmotion_interval_min_seconds} and "
                            f"{self.vmotion_interval_max_seconds}")
                wait_time = random.randint(self.vmotion_interval_min_seconds, self.vmotion_interval_max_seconds)

                # Sleep for 'wait_time'
                print(f"Waiting {wait_time} seconds")
                self._info(f"Sleeping for {wait_time} seconds")
                self.__exit.wait(wait_time)

                if not self.__exit.is_set():
                    # Perform random vMotions
                    print(f"Performing vMotions")
                    self._info(f"Performing random vMotions")
                    self.perform_vmotion()
                else:
                    # Stop requested during wait
                    print(f"Stop requested. Skipping vMotions")
                    self._info(f"Stop requested. Skipping vMotions")

        except VMotionatorException as e:
            self._critical(f"run: {e}")

        except Exception as e:
            self._critical(f"run: Unexpected exception: {e}")

        except:
            self._critical(f"run: Catch all exception!")

        finally:
            self._debug(f"run: Cleaning up")

    # noinspection PyUnusedLocal
    def stop(self, signum=None, frame=None):
        signame = signal.Signals(signum).name
        print(f"Received stop request ({signame})")
        self._debug(f"stop: Received stop request from {signame}")
        self.__exit.set()
