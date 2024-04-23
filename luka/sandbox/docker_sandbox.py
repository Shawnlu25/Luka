import docker
import time
import uuid
import os
import atexit

DEFAULT_IMAGE = "luka:1.0"
CONTAINER_NAME_PREFIX = "luka"

class DockerSandbox:
    def __init__(self, image: str=DEFAULT_IMAGE, timeout = 60):
        self.sid = str(uuid.uuid4())
        self.docker_client = docker.from_env()

        self.image_name = image
        self.container_name = f"{CONTAINER_NAME_PREFIX}-{self.sid}"

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
                command='tail -f /dev/null',
                network_mode='host',
                working_dir="/home/ubuntu/workspace",
                name=self.container_name,
                detach=True,
                tty=True,
                stdin_open=True,
                volumes={mount_dir: {'bind': "/home/ubuntu/workspace", 'mode': 'rw'}},
            )
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
        
        self.bash_socket = self.container.exec_run("/bin/bash", detach=False, tty=True, stdin=True, socket=True)[1]

    def _close(self):
        containers = self.docker_client.containers.list(all=True)
        for container in containers:
            try:
                if container.name.startswith(CONTAINER_NAME_PREFIX):
                    container.remove(force=True)
            except docker.errors.NotFound:
                pass

    def execute_command(self, command):
        s = self.bash_socket
        s._sock.send(command.encode('utf-8'))
    
    def fetch_output(self):
        output = b""
        while True:
            part = self.bash_socket._sock.recv(1024)
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
        sandbox.execute_command(cmd+"\n")
        print(sandbox.fetch_output())

    

exit()

def execute_detached_command(container, command):
    exec_instance = container.exec_run(command, detach=True)
    exec_id = exec_instance.id
    return exec_id

def fetch_exec_output(client, exec_id):
    return client.api.exec_start(exec_id, detach=False).decode('utf-8')
