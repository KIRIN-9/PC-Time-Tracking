#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Process filter module for PC Time Tracker
Filters processes based on various criteria
"""

import os
import re
import json
import platform
from typing import Dict, List, Any, Optional, Set
import psutil

class ProcessFilter:
    """
    Filter processes based on various criteria
    """

    DEFAULT_SETTINGS_PATH = os.path.expanduser("~/.pc_time_tracker/filter_settings.json")

    def __init__(self, settings_path: Optional[str] = None):
        self.settings_path = settings_path or self.DEFAULT_SETTINGS_PATH

        # Default settings
        self.excluded_processes: Set[str] = set()
        self.regex_patterns: List[str] = []
        self.process_priorities: Dict[str, int] = {}
        self.cpu_threshold: float = 0.1  # Default 0.1% CPU threshold
        self.memory_threshold: float = 0.1  # Default 0.1% memory threshold
        self.include_system_processes: bool = False

        # Load settings
        self.load_settings()

    def load_settings(self) -> None:
        """Load filter settings from file"""
        try:
            if not os.path.exists(self.settings_path):
                self._init_default_settings()
                self.save_settings()
                return

            with open(self.settings_path, 'r') as f:
                settings = json.load(f)

            self.excluded_processes = set(settings.get('excluded_processes', []))
            self.regex_patterns = settings.get('regex_patterns', [])
            self.process_priorities = settings.get('process_priorities', {})
            self.cpu_threshold = float(settings.get('cpu_threshold', 0.1))
            self.memory_threshold = float(settings.get('memory_threshold', 0.1))
            self.include_system_processes = bool(settings.get('include_system_processes', False))

        except Exception as e:
            print(f"Error loading filter settings: {e}")
            self._init_default_settings()

    def save_settings(self) -> None:
        """Save filter settings to file"""
        try:
            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)

            settings = {
                'excluded_processes': list(self.excluded_processes),
                'regex_patterns': self.regex_patterns,
                'process_priorities': self.process_priorities,
                'cpu_threshold': self.cpu_threshold,
                'memory_threshold': self.memory_threshold,
                'include_system_processes': self.include_system_processes
            }

            with open(self.settings_path, 'w') as f:
                json.dump(settings, f, indent=4)

        except Exception as e:
            print(f"Error saving filter settings: {e}")

    def _init_default_settings(self) -> None:
        """Initialize default filter settings"""
        system = platform.system()

        # Common system processes to exclude
        common_system_processes = {
            'svchost.exe', 'csrss.exe', 'dwm.exe', 'System', 'Registry', 'smss.exe',
            'wininit.exe', 'lsass.exe', 'services.exe', 'winlogon.exe', 'explorer.exe',
            'fontdrvhost.exe', 'spoolsv.exe', 'conhost.exe', 'RuntimeBroker.exe',
            'ShellExperienceHost.exe', 'SearchUI.exe', 'ctfmon.exe', 'taskhostw.exe',
            'SystemSettings.exe', 'sihost.exe', 'dllhost.exe'
        }

        linux_system_processes = {
            'systemd', 'kthreadd', 'kworker', 'kdevtmpfs', 'netns', 'rcu_tasks_kthre',
            'kauditd', 'khungtaskd', 'oom_reaper', 'writeback', 'kcompactd0', 'ksmd',
            'khugepaged', 'kintegrityd', 'kblockd', 'blkcg_punt_bio', 'tpm_dev_wq',
            'ata_sff', 'md', 'edac-poller', 'devfreq_wq', 'watchdogd', 'kswapd0',
            'ecryptfs-kthrea', 'kthrotld', 'acpi_thermal_pm', 'vfio-irqfd-clea',
            'ipv6_addrconf', 'kstrp', 'zswap-shrink', 'charger_manager', 'cron', 'NetworkManager',
            'systemd-journal', 'systemd-udevd', 'systemd-logind', 'thermald', 'accounts-daemon',
            'polkitd', 'wpa_supplicant', 'upowerd', 'irqbalanced', 'networkd-dispat', 'kerneloops',
            'dbus-daemon', 'rsyslogd', 'packagekitd', 'upstart', 'gnome-keyring-d', 'gdm3'
        }

        macos_system_processes = {
            'launchd', 'kernel_task', 'UserEventAgent', 'mds', 'mds_stores', 'WindowServer',
            'Dock', 'Finder', 'SystemUIServer', 'loginwindow', 'distnoted', 'mdworker',
            'airportd', 'coreaudiod', 'ssh-agent', 'securityd', 'launchservicesd', 'pboard',
            'nsurlsessiond', 'sharingd', 'opendirectoryd', 'amfid', 'configd', 'logind',
            'powerd', 'diskarbitrationd', 'nanoregistryd', 'usbmuxd', 'backupd', 'hidd',
            'cloudphotosd', 'secinitd', 'routined', 'diskmanagementd', 'spindump',
            'spotlight', 'mdinitializer', 'appleeventsd', 'netbiosd', 'syslogd', 'usbd'
        }

        # Set system-specific excluded processes
        if system == 'Windows':
            self.excluded_processes = common_system_processes
        elif system == 'Linux':
            self.excluded_processes = linux_system_processes
        elif system == 'Darwin':  # macOS
            self.excluded_processes = macos_system_processes
        else:
            self.excluded_processes = set()

        # Default regex patterns (match common system process patterns)
        self.regex_patterns = [
            r'^kworker/\d+:\d+$',  # Linux kernel workers
            r'^ksoftirqd/\d+$',     # Linux kernel IRQ handlers
            r'^migration/\d+$',     # Linux CPU migration processes
            r'^watchdog/\d+$',      # Linux watchdog processes
            r'^scsi_\w+$',          # SCSI subsystem processes
            r'^irq/\d+-.+$',        # IRQ handler processes
        ]

        # Default process priorities
        self.process_priorities = {
            'chrome': 2,
            'firefox': 2,
            'safari': 2,
            'code': 3,
            'vscode': 3,
            'idea': 3,
            'pycharm': 3,
            'eclipse': 3,
            'terminal': 3,
            'bash': 3,
            'zsh': 3,
            'powershell': 3,
            'cmd': 3,
            'slack': 2,
            'discord': 2,
            'zoom': 2,
            'teams': 2,
            'outlook': 2,
            'word': 2,
            'excel': 2,
            'powerpoint': 2,
            'photoshop': 3,
            'illustrator': 3,
            'spotify': 1,
            'steam': 1,
            'vlc': 1
        }

        # Default thresholds
        self.cpu_threshold = 0.1
        self.memory_threshold = 0.1
        self.include_system_processes = False

    def should_include_process(self, process: psutil.Process) -> bool:
        """
        Determine if a process should be included based on filter criteria

        Args:
            process: The process to check

        Returns:
            bool: True if the process should be included, False otherwise
        """
        try:
            # Get process info
            proc_info = process.info if hasattr(process, 'info') else {}
            name = proc_info.get('name', '') if proc_info else process.name()

            # Check if explicitly excluded
            if name in self.excluded_processes:
                return False

            # Check regex patterns
            for pattern in self.regex_patterns:
                if re.match(pattern, name):
                    return False

            # Check resource thresholds
            cpu_percent = proc_info.get('cpu_percent', 0) if proc_info else process.cpu_percent(interval=0.1)
            memory_percent = proc_info.get('memory_percent', 0) if proc_info else process.memory_percent()

            if cpu_percent < self.cpu_threshold and memory_percent < self.memory_threshold:
                return False

            # Check if system process
            if not self.include_system_processes:
                # Heuristics for system processes (adjust as needed)
                if platform.system() == 'Windows':
                    try:
                        # Windows system processes often run as SYSTEM or have special paths
                        username = process.username()
                        if 'SYSTEM' in username or 'LOCAL SERVICE' in username or 'NETWORK SERVICE' in username:
                            return False
                    except:
                        pass
                elif platform.system() == 'Linux':
                    try:
                        # Linux system processes often run as root or system users
                        username = process.username()
                        if username == 'root' or username.startswith('system'):
                            cmdline = process.cmdline()
                            # Consider system processes with no command line or typical system paths
                            if not cmdline or any(p in ' '.join(cmdline) for p in ['/lib/systemd', '/usr/sbin', '/usr/lib']):
                                return False
                    except:
                        pass
                elif platform.system() == 'Darwin':  # macOS
                    try:
                        # macOS system processes often run as root or system users
                        username = process.username()
                        if username == 'root' or username == '_mdnsresponder' or username == '_windowserver':
                            return False
                    except:
                        pass

            return True

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False
        except Exception as e:
            print(f"Error filtering process {getattr(process, 'name', lambda: 'unknown')()}: {e}")
            return False

    def get_process_priority(self, process: psutil.Process) -> int:
        """
        Get the priority of a process

        Args:
            process: The process to check

        Returns:
            int: Priority level (higher is more important)
        """
        try:
            name = process.info['name'] if hasattr(process, 'info') and 'name' in process.info else process.name()

            # Check for exact match
            if name.lower() in self.process_priorities:
                return self.process_priorities[name.lower()]

            # Check for partial match
            for proc_name, priority in self.process_priorities.items():
                if proc_name.lower() in name.lower():
                    return priority

            return 0  # Default priority

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return 0
        except Exception:
            return 0

    def exclude_process(self, process_name: str) -> None:
        """
        Add a process to the excluded list

        Args:
            process_name: Name of the process to exclude
        """
        self.excluded_processes.add(process_name)
        self.save_settings()

    def include_process(self, process_name: str) -> None:
        """
        Remove a process from the excluded list

        Args:
            process_name: Name of the process to include
        """
        if process_name in self.excluded_processes:
            self.excluded_processes.remove(process_name)
            self.save_settings()

    def add_regex_pattern(self, pattern: str) -> None:
        """
        Add a regex pattern for exclusion

        Args:
            pattern: Regex pattern to add
        """
        if pattern not in self.regex_patterns:
            try:
                # Validate regex
                re.compile(pattern)
                self.regex_patterns.append(pattern)
                self.save_settings()
            except re.error:
                raise ValueError(f"Invalid regex pattern: {pattern}")

    def remove_regex_pattern(self, pattern: str) -> None:
        """
        Remove a regex pattern

        Args:
            pattern: Regex pattern to remove
        """
        if pattern in self.regex_patterns:
            self.regex_patterns.remove(pattern)
            self.save_settings()

    def set_process_priority(self, process_name: str, priority: int) -> None:
        """
        Set the priority for a process

        Args:
            process_name: Name of the process
            priority: Priority level (higher is more important)
        """
        self.process_priorities[process_name.lower()] = priority
        self.save_settings()

    def remove_process_priority(self, process_name: str) -> None:
        """
        Remove the priority setting for a process

        Args:
            process_name: Name of the process
        """
        if process_name.lower() in self.process_priorities:
            del self.process_priorities[process_name.lower()]
            self.save_settings()

    def set_cpu_threshold(self, threshold: float) -> None:
        """
        Set the CPU usage threshold

        Args:
            threshold: CPU usage threshold in percent (0-100)
        """
        self.cpu_threshold = max(0.0, min(100.0, threshold))
        self.save_settings()

    def set_memory_threshold(self, threshold: float) -> None:
        """
        Set the memory usage threshold

        Args:
            threshold: Memory usage threshold in percent (0-100)
        """
        self.memory_threshold = max(0.0, min(100.0, threshold))
        self.save_settings()

    def set_include_system_processes(self, include: bool) -> None:
        """
        Set whether to include system processes

        Args:
            include: Whether to include system processes
        """
        self.include_system_processes = include
        self.save_settings()

    def reset_to_defaults(self) -> None:
        """Reset all filter settings to defaults"""
        self._init_default_settings()
        self.save_settings()