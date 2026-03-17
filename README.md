# Mirage

## Overview
Mirage is a Red Team operational toolkit for Windows, Linux, and FreeBSD environments that deploys and manages compromised web servers for offensive operations. The toolkit allows operators to establish and maintain access through remote code execution, reverse shells, privilege escalation, and persistence mechanisms. It includes:

- **Ansible Playbooks and Roles**: Automates deploy/undeploy workflows across Windows Server, Windows 10, Linux, and FreeBSD targets
- **Extensions**: Provides additional fun functionality to Mirage that can be deployed alongside the main ansible workflow.
- **PHP Scripts**: Supports hosted payload handling and web-side execution workflows
- **Website Content**: Includes competition-themed HTML assets and supporting image sets for social engineering scenarios
- **Persistence Mechanisms**: A Windows service used for maintaining long-term access and preventing remediation
- **Python Controller**: A Centralized command-line interface with modular `Server/` components used for singular and mass execution, shell deployment, callbacks, and much more

### Directory Breakdown
- **`Ansible/`**: Deployment and undeployment automation (`playbooks/deploy.yml`, `playbooks/undeploy.yml`) with per-platform roles (`windowsServer`, `windows10`, `linux`, `freebsd`) and extension role support (`puzzler`).
- **`Server/` + `mirage.py`**: Interactive operator workflow for singular/mass command execution, reverse shell orchestration, callback testing/visualization, and host-group targeting from config.
- **`Website/`, `Images/`, and `PHP/`**: Hosted web surface and competition-specific site variants used for payload interaction and response handling.
- **`Persistence/`**: Windows persistence service source and related build artifacts.
- **`Extensions/`**: Optional capability modules (for example, `Puzzler`) that can be deployed alongside baseline Mirage functionality.

## Setup Instructions

### Prerequisites
- **Ansible**: Installed on the control machine.
- **Network Configuration**: Make sure all hosts are accessible (SSH, WinRM) and that required ports are properly configured.
- **Required Packages**:
  ```sh
  sudo apt install git
  sudo apt install software-properties-common
  sudo add-apt-repository ppa:ansible/ansible --yes --update
  sudo apt install ansible
  sudo apt install python3-pip
  ```

### Steps

## 1. Clone the Repository and Install Requirements
```bash
cd ~
git clone https://github.com/Lcdemi/Mirage
pip install -r requirements.txt
ansible-galaxy collection install -r ansible-requirements.yml
cd Mirage/Ansible
```

## 2. Configure Ansible Inventory
Edit the inventory.yml file to include your server's details:

```yaml
all:
  vars:
    home_dir: "" # REPLACE WITH USER HOME DIRECTORY PATH
    competition: "" # REPLACE WITH COMPETITION NAME (EmpireStateHealth, IRSEC, UBLockdown, ISTSQuals)
  children:
    windows:
      vars:
        ansible_user: "" # REPLACE WITH WINDOWS USERNAME
        ansible_password: "" # REPLACE WITH WINDOWS PASSWORD
      children:
        windowsServer:
          hosts:
            # REPLACE WITH WINDOWS SERVER HOST IP ADDRESSES
        windows10:
          hosts:
            # REPLACE WITH WINDOWS 10 HOST IP ADDRESSES
    linux:
      vars:
        ansible_user: "" # REPLACE WITH LINUX USERNAME
        ansible_password: "" # REPLACE WITH LINUX PASSWORD
      hosts:
        # REPLACE WITH LINUX HOST IP ADDRESSES
    freebsd:
      vars:
        ansible_user: "" # REPLACE WITH FREEBSD USERNAME
        ansible_password: "" # REPLACE WITH FREEBSD PASSWORD
      hosts:
        # REPLACE WITH FREEBSD HOST IP ADDRESSES
```

## 3. Run the Ansible Playbook
From the repository root, run the deploy playbook:

```sh
ansible-playbook playbooks/deploy.yml --tags deploy
```

## 4. Using the Tool
Use `mirage.py` for interactive command execution, shell operations, callback testing, and host-group actions.

#### Configure config.json
Mirage uses `Server/config.json` to build target groups and runtime behavior. Update this file before running operations.

1. Set `hosts.range_start` and `hosts.range_end` to your environment range.
2. Set each pattern in `hosts.patterns` using `{x}` where the range value should be substituted.
3. Use `null` for any host group you do not want generated.
4. Set `other.PORT` to your web callback/listener port used by hosted payload endpoints.
5. Adjust `other.TIMEOUT`, `other.CONCURRENCY`, and `other.THROTTLE_MS` for reliability vs speed.
6. Add optional integrations under `logging` (`PWNBOARD_URL`, `PWNBOARD_AUTH_TOKEN`, `DISCORD_WEBHOOK_URL`).

Example:
```json
{
  "hosts": {
    "range_start": 1,
    "range_end": 13,
    "patterns": {
      "ALL_CA": null,
      "ALL_DC": "10.{x}.1.1",
      "ALL_FTP": null,
      "ALL_ICMP": "10.{x}.1.3",
      "ALL_IIS": "192.168.{x}.4",
      "ALL_MSSQL": null,
      "ALL_RDP": null,
      "ALL_SMB": "192.168.{x}.3",
      "ALL_SSH": null,
      "ALL_WINRM": "10.{x}.1.2"
    }
  },
  "logging": {
    "PWNBOARD_URL": "https://www.pwnboard.win/pwn",
    "PWNBOARD_AUTH_TOKEN": "Bearer AUTH_TOKEN_HERE",
    "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/FULL_WEBHOOK_HERE"
  },
  "other": {
    "PORT": 8080,
    "TIMEOUT": 30,
    "CONCURRENCY": 8,
    "THROTTLE_MS": 50,
    "TIMEZONE": "EST"
  }
}
```

#### Starting the Tool
```sh
cd Mirage
python3 mirage.py
```

#### Available Actions
1. **Singular Remote Code Execution**: Execute a command against one validated target
2. **Mass Remote Code Execution**: Execute a command across a selected target group
3. **Spawn a Reverse Shell**: Launch a listener and trigger shell callback from one validated target
4. **Reset Firewalls**: Reset firewalls against selected targets
5. **Disable Security & Monitoring Tools**: Apply IFEO debugger hijacks to common analysis tools
6. **Spawn Utility Backdoors**: Configure accessibility/utility executable debugger backdoors
7. **Drop SSH Keys (Coming Soon)**: Placeholder action (not implemented yet)
8. **Sinkhole Domains**: Sinkhole specified domains using DNS
9. **Test Connections**: Execute `whoami` callbacks and classify results
10. **View All Connections**: Display the callback summary dashboard

#### Example Usage
```bash
# Run a command across all IIS hosts
> Select "Mass Remote Code Execution"
> Choose "All IIS Hosts"
> Enter command: whoami /priv

# Trigger callback testing and review results
> Select "Test Connections"
> Choose "All WinRM Hosts"
> Confirm execution
> Select "View All Connections"

# Spawn reverse shell to a specific target
> Select "Spawn a Reverse Shell"
> Enter target: 192.168.4.3
> Enter listener: 10.65.0.10:6767
```