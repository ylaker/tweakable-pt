# DESCRIPTION

# INSTALLATION INSTRUCTIONS

Config file for tor on the client: /etc/tor/torrc-client

	UseBridges 1
	Log notice stdout
	DataDirectory /usr/local/var/lib/tor-client

	ExitPolicyRejectPrivate 0

	SOCKSPort 27000

	Bridge simple 127.0.0.1:9151

	ClientRejectInternalAddresses 0

	ClientTransportPlugin simple exec /home/yoann/MscInfoSec-Project/tweakable_pt/client.py

Config file for tor on the server: /etc/tor/torrc-server

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


To run tor on the client : "tor -f /etc/tor/torrc-client"

To run tor on the server : "tor -f /etc/tor/torrc-server"

Then ,on the client, connect an application to the tor listenning socks proxy on the port: 

	SOCKSPort 27000
