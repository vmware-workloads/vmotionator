# vmotionator
A simple Python3 / Linux systemd service to randomly vMotion some VM in a cluster.

## Authors
* Charles Lee
* Dharmesh Bhatt


## Requirements
* Ubuntu 24
* Python 3.12+


## Installation

### Curl
1. Run the following command on the target system command line.
```bash
# Download and run the installation script to install the latest release.
curl -sL https://raw.githubusercontent.com/vmware-workloads/vmotion-application-notification/main/remote.sh | bash
```

### Git Clone
1. Download and install the files.
```
git clone https://github.com/vmware-workloads/vmotionator.git
cd ./vmotionator
chmod a+x install.sh vmotionator.py
sudo ./install.sh
```
<br>

3. Configure the service by editing the vmnotification.conf file.
```ini
# /etc/vmotionator/vmotionator.conf

# All the commented options have the default values.
# To change an option, uncomment the line and set
# the desired value(s)

[SERVER]
# vCenter Server
# ---> These 3 fields are mandatory <---
vcenter_server = <your vc server>
vcenter_username = <username>
vcenter_password = <password>

# Set this option to 'no' to skip the vCenter SSL certificate validation
#vcenter_ssl_verify = no

# Should be left at 443 unless the vCenter HTTPS port was changed
#vcenter_port = 443


[DEFAULT]
# We perform a vmotion between MIN and MAX interval times.
#vmotion_interval_min_seconds = 900      # 15 minutes
#vmotion_interval_max_seconds = 1200     # 20 minutes

# Number of VM that we perform a random VM
#vmotion_vm_count = 1

# VM Exclusions
#vmotion_vm_exclusions =
#    vCLS
#    SupervisorControlPlaneVM
#    vSAN File Service Node

[LOGGING]
# Log files
#service_logfile = /var/log/vmotionator/service.log
#vmotion_logfile = /var/log/vmotionator/vmotion.log

# Logging verbosity in the service log file
#service_logfile_level  = DEBUG

# Logging verbosity in the service console
#service_console_level  = WARNING

# Maximum size of the log file in Bytes
#service_logfile_maxsize_bytes = 10485760
#vmotion_logfile_maxsize_bytes = 10485760

# Number of log files to keep (.log, .log.1, .log.2, ...). Once this number of log files
# is reached, the oldest file is deleted.
#service_logfile_count = 10
#vmotion_logfile_count = 10
```
<br>

4. Restart the service.
```
sudo systemctl restart vmotionator.service
```

## Files and Paths

#### vmotionator.py
* description: Service launcher.
* path: /opt/vmotionator/vmotionator.py

#### vmotionator.service
* description: The systemd service file.
* path: /etc/systemd/system/vmotionator.service

#### vmotionator
* description: The systemd service options file.
* path: /etc/default/vmotionator

#### vmotionator.conf
* description: Service configuration. This file contains the command and options for the service.
* path: /etc/vmotionator/vmotionator.conf
* should edit?: **YES**

#### service.log
* description: Service log file.
* path: /var/log/vmotionator/service.log

#### vmotion.log
* description: vMotion log file.
* path: /var/log/vmotionator/vmotion.log
