import abc
import argparse
import os
from src import util
import json
import getpass
from argparse import ArgumentError
from typing import Iterator, Protocol


class SystemStrategy(Protocol):
    @abc.abstractmethod
    def get_config_file_path(self) -> str:
        pass

    @abc.abstractmethod
    def save(self, data: util.ConfigFile) -> None:
        pass

    @abc.abstractmethod
    def clear_screen(self) -> None:
        pass


class Model(metaclass=util.MetaSingleton):
    def __init__(self, system_strategy: SystemStrategy):
        self._system_strategy = system_strategy

        if not os.path.exists(self.get_config_file_path()):
            if not os.path.exists(os.path.dirname(self.get_config_file_path())):
                os.makedirs(os.path.dirname(self.get_config_file_path()))
            with open(self.get_config_file_path(), "a") as f:
                f.write("""{"groups":[]}""")

        with open(self.get_config_file_path(), "r") as f:
            try:
                self._config_dict: util.ConfigFile = json.loads(f.read())
            except json.decoder.JSONDecodeError:
                with open(self.get_config_file_path(), "a") as f:
                    f.write("""{"groups":[]}""")
                self._config_dict: util.ConfigFile = {"groups": []}

        self.names_set: set[str] = {i.get("name") for i in self._config_dict["groups"]}

    def get_groups(self) -> Iterator[util.ModGroup]:
        return (i for i in self._config_dict["groups"])

    def add_group(self, group: util.ModGroup) -> None:
        if group["name"] in self.names_set:
            raise ArgumentError(None, f"name {group['name']} is already used")
        elif group["mod_loader"] not in util.modloaders:
            raise ArgumentError(None, f"The only valid modloaders are {util.modloaders}, not {group['mod_loader']}")

        self._config_dict["groups"].append(group)
        self.names_set.add(group['name'])

    def remove_group(self, group_name: str):
        if not group_name in self.names_set:
            raise argparse.ArgumentError(None, f"{group_name} was not found")

        self._config_dict['groups'] = [i for i in self._config_dict['groups'] if i['name'] != group_name]
        self.names_set.remove(group_name)

    def get_config_file_path(self) -> str:
        return self._system_strategy.get_config_file_path()

    def save(self) -> None:
        self._system_strategy.save(self._config_dict)

    def clear_screen(self):
        self._system_strategy.clear_screen()


class LinuxStategy(SystemStrategy):
    def get_config_file_path(self) -> str:
        return f"/home/{getpass.getuser()}/.config/minecraft-mod-config.json"

    def save(self, data: util.ConfigFile) -> None:
        with open(self.get_config_file_path(), "w") as f:
            f.write(json.dumps(data, indent=2))

    def clear_screen(self):
        os.system("clear")


def get_model() -> Model:
    """:returns the correct model corresponding to the platform"""
    try: return Model()
    except TypeError: return Model(LinuxStategy())