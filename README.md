# Mirage

## Overview
Mirage is a Red Team operational toolkit for Windows environments that deploys and manages compromised IIS servers for offensive operations. The toolkit allows operators to establish and maintain access through remote code execution, reverse shells, privilege escalation, and persistence mechanisms. It includes:

- **Ansible Playbooks**: Automate the deployment and configuration of IIS servers across multiple targets
- **PHP Scripts**: Facilitate reverse shell functionality and SYSTEM privilege escalation
- **Website Content**: Professional-looking HTML and assets for social engineering
- **Persistence Mechanisms**: C++ Windows service for maintaining long-term access
- **Python Controller**: Centralized command-line interface for managing mass RCE operations and reverse shell deployment

## Repository Structure

<pre>Mirage/
├── Ansible/
│   ├── inventory
│   │   └── inventory.yml
│   ├── roles
│   │   ├── windows10
│   │   │   └── tasks
│   │   │       └── main.yml
│   │   └── windowsServer
│   │       └── tasks
│   │           └── main.yml
│   ├── playbook.yml
│   └── ansible.cfg
├── Images/
│   ├── UBLockdown/
│   ├── IRSEC/
│   └── EmpireStateHealth/
├── PHP/
│   ├── contact.php
│   ├── search.php
│   └── php.ini
├── Persistence/
│   ├── Main.cpp
│   ├── Service.h
│   ├── Service.cpp
│   ├── Persistence.h
│   ├── Persistence.cpp
│   └── IISManagerService.exe
├── Website/
│   ├── UBLockdown/
│   │   ├── UBLockdown.html
│   │   ├── button.js
│   │   └── web.config
│   ├── IRSEC/
│   │   ├── IRSEC.html
│   │   ├── button.js
│   │   └── web.config
│   └── Empire State Health/
│       ├── EmpireStateHealth.html
│       ├── button.js
│       └── web.config
└── mirage.py
</pre>

### Directory Breakdown
- **`Ansible/`**: Contains playbooks and inventory files for automating server setup.
- **`Images/`**: Directory with images used in the website.
- **`PHP/`**: Contains the PHP script for the reverse shell.
- **`Persistence/`**: Contains the C++ executable service that maintains persistence on the server.
- **`Website/`**: HTML and CSS files for the website's frontend.
- **`mirage.py`**: A Python Client that can be utilized for Remote Code Execution and Shell Creation.

## Setup Instructions

### Prerequisites
- **Ansible**: Installed on the control machine.
- **Windows Server**: With WinRM running and enabled.
- **Network Configuration**: Make sure the server is accessible and that required ports are properly configured.
- **Required Packages**:

  ```sh
  sudo apt install git
  sudo apt install software-properties-common
  sudo add-apt-repository ppa:ansible/ansible --yes --update
  sudo apt install ansible
  sudo apt install python3-pip
  pip install inquirerpy
  pip install rich
  pip install pyfiglet
  ```

### Steps

## 1. Clone the Repository
```bash
cd ~
git clone https://github.com/Lcdemi/Mirage
cd Mirage/Ansible
```

## 2. Configure Ansible Inventory
Edit the inventory.yml file to include your server's details:

```yaml
all:
  vars:
    ansible_user: "" # REPLACE WITH USERNAME
    ansible_password: "" # REPLACE WITH PASSWORD
    ansible_connection: winrm
    ansible_port: 5985
    ansible_winrm_transport: ntlm
    ansible_winrm_server_cert_validation: ignore
    home_dir: "" # REPLACE WITH USER HOME DIRECTORY PATH
    competition: "" # REPLACE WITH COMPETITION NAME (Options: EmpireStateHealth, IRSEC, UBLockdown)
  children:
    windowsServer:
      hosts:
        # REPLACE WITH WINDOWS SERVER IP ADDRESSES
    windows10:
      hosts:
        # REPLACE WITH WINDOWS 10 IP ADDRESSES
```

## 3. Run the Ansible Playbook
To set up the IIS server and deploy the website, execute the following command:

```sh
ansible-playbook playbook.yml --tags windows
```

## 4. Using the Tool
For remote command execution and reverse shell deployment, use the included `mirage.py` Python tool.

### Features
- **Singular Command Execution**: Run commands on individual targets
- **Mass Command Execution**: Execute commands across multiple targets simultaneously
- **Reverse Shell Deployment**: Spawn reverse shells to your listener
- **Target Group Management**: Pre-defined groups for different host types
- **Real-time Results**: Live output from all connected systems

### Usage

#### Starting the Tool
```sh
python3 mirage.py
```

#### Available Actions
1. **Singular Remote Code Execution:** Execute commands on single targets
2. **Mass Remote Code Execution:** Run commands across target groups
3. **Spawn a Reverse Shell:** Deploy reverse shells

#### Target Groups
- All Hosts
- Domain Controllers
- IIS Hosts
- WinRM Hosts
- ICMP Hosts
- SMB Hosts
- Custom Targets (Manual IP input)

Note: The target IP addresses in server.py are pre-configured for a specific network environment (192.168.X.X and 10.X.1.X ranges). You may need to modify the ALL_HOSTS, ALL_DC, ALL_IIS, ALL_WINRM, ALL_ICMP, and ALL_SMB arrays in the `mirage.py` script to match your target network configuration.

#### Example Usage
```bash
# Check privileges across all IIS servers
> Select "Mass Remote Code Execution"
> Choose "All IIS Hosts"
> Enter command: whoami /priv

# Deploy reverse shell to specific target
> Select "Spawn a Reverse Shell"
> Enter target: 192.168.4.3
> Enter listener: 10.65.0.10:6767
```
