import ptyprocess
import os
import atexit
import time

class LocalSandbox:
    def __init__(self, timeout: int = 120, cwd: str = None):
        self.timeout = timeout
        self.cwd = cwd if cwd else os.getcwd()
        self.session = ptyprocess.PtyProcess.spawn(
            ["bash"], 
            cwd=self.cwd, 
            env={
                "PS1": rb"\[\](sandbox) \[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ ",
                "TERM": "xterm-256color"
                }
        )
        
        atexit.register(self._cleanup)
        
    def _reset(self):
        self._cleanup()
        self.session = ptyprocess.PtyProcess.spawn(
            ["bash"], 
            cwd=self.cwd, 
            env={
                "PS1": rb"\[\](sandbox) \[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ ",
                "TERM": "xterm-256color"
                }
        )
    
    def _cleanup(self):
        self.session.terminate(force=True)

    def send_command(self, command: str):
        command = command.strip()
        self.session.write(command.encode("utf-8") + b"\n")
    
    def fetch_output(self):
        output = b""
        while True:
            part = self.session.read(1024)
            output += part
            if len(part) < 1024:
                break
        return output.decode("utf-8")
        
if __name__ == "__main__":
    sandbox = LocalSandbox()
    while True:
        cmd = input("> ")
        if cmd == "exit":
            break
        elif cmd.startswith("CTRL-"):
            ch = cmd.split("-")[1].lower()
            # convert ascii character to control character
            ch = chr(ord(ch) - ord('a') + 1)
            sandbox.send_command(ch)
            continue
        sandbox.send_command(cmd)
        time.sleep(0.5)
        print(sandbox.fetch_output())
        
    