"""Headless manual interface for the same simulated model; no external tools."""
from providers.builtin import BuiltinProvider


def main():
    provider = BuiltinProvider()
    lab = provider.lab
    print("NetForge SIMULATED lab. help for commands; no host network commands run.")
    while True:
        try:
            line = input("netforge> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        try:
            if line in ("quit", "exit"):
                break
            if line == "help":
                print("status | connect | disconnect | ping | cli <switch command> | assess | reset | quit")
            elif line == "status":
                print(lab.state())
            elif line == "connect":
                lab.connect("pc-b:eth0", "sw1:fa0/3")
                print("Cable connected")
            elif line == "disconnect":
                lab.disconnect("pc-b:eth0")
                print("Cable disconnected")
            elif line == "ping":
                print("Success" if lab.ping("pc-b:eth0", "pc-a:eth0") else "Failed")
                print("\n".join(lab.traces))
            elif line.startswith("cli "):
                print(provider.execute_command("sw1", line[4:]))
            elif line == "assess":
                print(lab.assess())
            elif line == "reset":
                lab.reset()
                print("Reset")
            else:
                print("Unknown command; help for commands")
        except ValueError as exc:
            print("Error:", exc)


if __name__ == "__main__":
    main()
