* trunk-tap.py
A clean and efficient way to transport VLANs over a TINC/OpenVPN TAP-interface.


## Introduction
trunk-tap.py is a Linux command line utility to connects a set of 802.1Q VLANs to a TINC VPN/OpenVPN TAP-interface and is designed to be invoked by ifup/ifdown scripts after starting or stoppping a VPN connection.
Dependencies (on Debian): python3, iproute2, bridge-utils, vlan (including kernel module '8021q' in /etc/modules)
It reads the filenames from the content of folder containing files corresponding to the VLAN ID (e.g. '100', '105', ...), then creates VLAN interfaces on a local Ethernet adapter used as "trunk port" (e.g. 'eth1.100', 'eth1.105', ...).
The script then proceeds to generate bridge interfaces for every VLAN ID. (e.g. "trunk0.100", "trunk0.105", ...) and attaches the respective Ethernet VLAN interfaces to the bridge. (e.g. 'trunk0.105 <-> eth1.105', ...)
After that, the local infrastructure is ready to be attached to the VPN layer 2 tunnel.
This is achieved by enabling the TAP interface ("up"), creating VLAN interfaces on the TAP adapter (e.g. 'tap0.100', 'tap0.105', ...) and attaching them to the respective bridge.


## Illustration

```
                              (TINC VPN / OpenVPN)
 -------- SITE 1 -------                                -------- SITE 2 -------
 eth1.100 <-> trunk0.100 <--\   ################   /--> trunk0.100 <-> eth1.100
 eth1.105 <-> trunk0.105 <--->> ---TAP-TUNNEL--- <<---> trunk0.105 <-> eth1.105
 eth1.110 <-> trunk0.110 <--/   ################   \--> trunk0.110 <-> eth1.110

 Hint: Interface names (ethernet adapter, bridge name, ...) do not neccesarily have to be identical among sites.

```

## License
This script is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
