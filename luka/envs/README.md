# Setup Docker

## Check Default Bridge Network
Docker automatically creates a default bridge network (docker0) when installed. You can inspect this network by running:
```bash
docker network inspect bridge
```
This command shows you the configuration of the default bridge network. Pay attention to the Subnet and Gateway.

## Ensure NAT is Enabled
The most common issue with Docker containers not accessing the internet is the lack of IP Masquerading (NAT). This setting allows containers to share the host's IP address to access external networks. Check if IP Masquerade is enabled on your system's firewall. Here’s how you can enable it using iptables on Linux:
```bash
sudo iptables -t nat -A POSTROUTING -s 172.17.0.0/16 -o eth0 -j MASQUERADE
```
Replace 172.17.0.0/16 with the subnet of your Docker bridge network (check from the docker network inspect bridge output), and eth0 with your host's main outbound network interface.


## Configure DNS Settings
Docker containers use the same DNS servers as the host by default. If there's a DNS misconfiguration, containers might not be able to resolve domain names. You can specify DNS servers for Docker by adding them to the Docker daemon configuration file (/etc/docker/daemon.json):

```json
{
  "dns": ["8.8.8.8", "8.8.4.4"] // Google DNS servers
}
```
