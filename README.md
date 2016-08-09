# TWEAKABLE COMPONENT ARCHITECTURE

## DESCRIPTION
This is an implementation of a modular architecture for Tor's Pluggable Transport based on the specification made by the tor project.

https://gitweb.torproject.org/sjm217/torspec.git/tree/pt-components.txt?h=pt-components

## INSTALLATION INSTRUCTIONS

### PREREQUISITIES

There is several prerequisities to be able to run this project, here is what must be installed:
* tor
* python
* pyptlib
* twisted
* pytest

### CONFIGURING THIS PT

You can clone this project by running:
```
$ git clone https://gitlab.com/MscProject-YLaker/tweakable-pt.git
```

Edit the config files inside
```
/path/to/the/dir/tweakable_pt/config
```

### CONFIGURING TOR
Config file for tor on the client: /etc/tor/torrc-client

```
UseBridges 1
Log notice stdout
DataDirectory /usr/local/var/lib/tor-client

ExitPolicyRejectPrivate 0

SOCKSPort 27000

Bridge simple 127.0.0.1:9151

ClientRejectInternalAddresses 0

ClientTransportPlugin simple exec /home/yoann/MscInfoSec-Project/tweakable_pt/client.py
```

Config file for tor on the server: /etc/tor/torrc-server

```
BridgeRelay 1

SocksPort 0
SocksListenAddress 127.0.0.1 
ORPort 9055
ExtORPort 41000

ExitPolicyRejectPrivate 0

Log notice stdout
DataDirectory /usr/local/var/lib/tor-bridge

Exitpolicy reject *:*
RefuseUnknownExits 1

AssumeReachable 1
PublishServerDescriptor 0
ServerTransportListenAddr simple 127.0.0.1:9045
ServerTransportPlugin simple exec /home/yoann/MscInfoSec-Project/tweakable_pt/server.py
```

### RUNNING TOR

To run tor on the client :
```
$ tor -f /etc/tor/torrc-client
```
To run tor on the server : 
```
$ tor -f /etc/tor/torrc-server
```

Then ,on the client, connect an application to the tor listenning socks proxy on the port: 

```
SOCKSPort 27000
```