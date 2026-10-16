"""Provider boundary: real runtimes must implement capability checks explicitly."""
from __future__ import annotations
from abc import ABC, abstractmethod


class UnsupportedOperation(RuntimeError):
    pass


class LabProvider(ABC):
    @abstractmethod
    def capabilities(self) -> dict[str, bool]: ...

    def create_lab(self): raise UnsupportedOperation("Provider cannot create a lab")
    def start_lab(self): raise UnsupportedOperation("Provider cannot start a lab")
    def stop_lab(self): raise UnsupportedOperation("Provider cannot stop a lab")
    def connect_interfaces(self, a: str, b: str): raise UnsupportedOperation("Provider cannot connect interfaces")
    def execute_command(self, device: str, command: str): raise UnsupportedOperation("Provider cannot execute commands")
    def capture_packets(self): raise UnsupportedOperation("Provider cannot capture real packets")
    def read_device_state(self): raise UnsupportedOperation("Provider cannot read state")
    def validate_connectivity(self, a: str, b: str): raise UnsupportedOperation("Provider cannot validate connectivity")
    def save_checkpoint(self): raise UnsupportedOperation("Provider cannot save a checkpoint")
    def restore_checkpoint(self, checkpoint_id: int | None = None): raise UnsupportedOperation("Provider cannot restore a checkpoint")
    def destroy_lab(self): raise UnsupportedOperation("Provider cannot destroy a lab")
