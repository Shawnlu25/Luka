import docker
import time
import uuid
import os
import atexit

DEFAULT_IMAGE = "luka:1.0"
DEFAULT_RUNTIME = "runsc"
DEFAULT_HOME_DIR = "/home/ubuntu"
CONTAINER_NAME_PREFIX = "luka"

class DockerSandbox:
    def __init__(self, image: str=DEFAULT_IMAGE, window_size=(24, 80), timeout = 60):
        self.sid = str(uuid.uuid4())
        self.docker_client = docker.from_env()

        self.image_name = image
        self.container_name = f"{CONTAINER_NAME_PREFIX}-{self.sid}"

        self.window_size = window_size
        self.timeout = timeout
        self._restart_container()

        atexit.register(self._close)

    def _is_container_running(self):
        try:
            container = self.docker_client.containers.get(self.container_name)
            if container.status == 'running':
                self.container = container
                return True
            return False
        except docker.errors.NotFound:
            return False

    def _stop_container(self):
        if not self._is_container_running():
            return
        container = self.docker_client.containers.get(self.container_name)
        container.stop()
        container.remove()
        elapsed = 0
        while container.status != 'exited':
            time.sleep(1)
            elapsed += 1
            if elapsed > self.timeout:
                break
            try:
                container = self.docker_client.containers.get(self.container_name)
            except docker.errors.NotFound:
                break

    def _restart_container(self):
        self._stop_container()
        mount_dir = os.environ["LUKA_TEMP_DIR"]
        try:
            self.container = self.docker_client.containers.run(
                self.image_name,
                command="/bin/bash",
                network_mode='bridge',
                working_dir= DEFAULT_HOME_DIR + "/workspace",
                name=self.container_name,
                runtime=DEFAULT_RUNTIME, 
                detach=True,
                tty=True,
                stdin_open=True,
                volumes={mount_dir: {'bind': DEFAULT_HOME_DIR + "/workspace", 'mode': 'rw'}},
            )
            self.container.resize(height=self.window_size[0], width=self.window_size[1])
        except Exception as e:
            raise e
        
        elapsed = 0
        while self.container.status != 'running':
            if self.container.status == 'exited':
                break
            time.sleep(1)
            elapsed += 1
            self.container = self.docker_client.containers.get(self.container_name)
            if elapsed > self.timeout:
                break
        if self.container.status != 'running':
            raise Exception('Failed to start container')
        
        self.bash_socket = self.docker_client.api.attach_socket(self.container.id, params={'stdin': 1, 'stdout': 1, 'stderr': 1, 'stream': 1})
        self.bash_socket._sock.setblocking(False)


    def _close(self):
        containers = self.docker_client.containers.list(all=True)
        for container in containers:
            try:
                if container.name.startswith(CONTAINER_NAME_PREFIX):
                    container.remove(force=True)
            except docker.errors.NotFound:
                pass

    def send_command(self, command):
        s = self.bash_socket
        s._sock.sendall(command.encode('utf-8'))
    
    def fetch_output(self):
        output = b""
        while True:
            try:
                part = self.bash_socket._sock.recv(1024)
            except BlockingIOError:
                part = b""
            output += part
            if len(part) < 1024:
                break
        return output.decode('utf-8')


if __name__ == "__main__":
    sandbox = DockerSandbox()
    
    while True:
        cmd = input("> ")
        cmd = cmd.strip()
        if cmd == "exit":
            break
        elif cmd.startswith("CTRL-"):
            ch = cmd.split("-")[1].lower()
            # convert ascii character to control character
            ch = chr(ord(ch) - ord('a') + 1)
            sandbox.send_command(ch)
            continue
        sandbox.send_command(cmd+"\n")
        time.sleep(0.5)
        print(sandbox.fetch_output())
