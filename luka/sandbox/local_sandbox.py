import ptyprocess
import os
import atexit

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
        
        atexit.register(self.cleanup)
        
    def reset(self):
        self.cleanup()
        self.session = ptyprocess.PtyProcess.spawn(
            ["bash"], 
            cwd=self.cwd, 
            env={
                "PS1": rb"\[\](sandbox) \[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ ",
                "TERM": "xterm-256color"
                }
        )
    
    def cleanup(self):
        self.session.terminate(force=True)

    def execute(self, command: str):
        command = command.strip()
        self.session.write(command.encode("utf-8") + b"\n")
        self.session.write(b"echo -e ''\n")
        output = []
        while True:
            line = self.session.readline().decode("utf-8")
            if "echo -e ''" in line:
                line = self.session.readline()
                break
            output.append(line)
        print(''.join(output).strip())
        

if __name__ == "__main__":
    sandbox = LocalSandbox()
    while True:
        cmd = input("> ")
        if cmd == "exit":
            break
        sandbox.execute(cmd)
        
    