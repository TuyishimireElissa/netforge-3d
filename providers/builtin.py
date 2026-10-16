"""Builtin simulated provider; optional SQLite state/checkpoints, never host commands."""
from database.store import SQLiteStore, PersistenceError
from providers.base import LabProvider, UnsupportedOperation
from simulation.core import Lab


class BuiltinProvider(LabProvider):
    def __init__(self, store: SQLiteStore | None = None):
        self.store = store
        self.lab = store.load_active() if store else None
        if self.lab is None:
            self.lab = Lab(durable=store is not None)
            self.persist()

    def persist(self) -> None:
        if self.store:
            self.store.save_active(self.lab)

    def capabilities(self) -> dict[str, bool]:
        return {"simulated_ethernet": True, "simulated_ipv4_ping": True, "switch_cli": True,
                "real_tools": False, "real_capture": False, "isolated_runtime": False,
                "persistent_checkpoint": self.store is not None}

    def create_lab(self):
        self.lab.reset()
        self.persist()
        return self.read_device_state()

    def start_lab(self): return self.read_device_state()
    def stop_lab(self): raise UnsupportedOperation("Simulation is local; no runtime to stop")
    def connect_interfaces(self, a: str, b: str): self.lab.connect(a, b)
    def execute_command(self, device: str, command: str):
        if device != "sw1": raise UnsupportedOperation("Only simulated switch CLI is available")
        return self.lab.cli.execute(command)
    def read_device_state(self):
        state = self.lab.state()
        state["checkpoints"] = self.store.list_checkpoints() if self.store else []
        return state
    def validate_connectivity(self, a: str, b: str): return self.lab.ping(a, b)
    def save_checkpoint(self):
        if not self.store: raise UnsupportedOperation("Start bridge with SQLite for checkpoints")
        return self.store.save_checkpoint(self.lab)
    def restore_checkpoint(self, checkpoint_id: int | None = None):
        if not self.store: raise UnsupportedOperation("Start bridge with SQLite for checkpoints")
        self.lab = self.store.load_checkpoint(checkpoint_id)
        self.persist()
        return self.read_device_state()
    def delete_checkpoint(self, checkpoint_id: int):
        if not self.store: raise UnsupportedOperation("Start bridge with SQLite for checkpoints")
        self.store.delete_checkpoint(checkpoint_id)
    def destroy_lab(self): self.create_lab()
