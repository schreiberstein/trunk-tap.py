# trunk-tap.py
A clean and efficient way to transport VLANs over a TINC/OpenVPN TAP-interface.


## Introduction
trunk-tap.py is a Linux command line utility to connects a set of 802.1Q VLANs to a TINC VPN/OpenVPN TAP-interface
and is designed to be invoked by ifup/ifdown scripts after starting or stoppping a VPN connection.

It reads the filenames from the content of folder containing files corresponding to the VLAN ID (e.g. '100', '105', ...),
then creates VLAN interfaces on a local Ethernet adapter used as "trunk port" (e.g. 'eth1.100', 'eth1.105', ...).

The script then proceeds to generate bridge interfaces for every VLAN ID. (e.g. "trunk0.100", "trunk0.105", ...)
and attaches the respective Ethernet VLAN interfaces to the bridge. (e.g. 'trunk0.105 <-> eth1.105', ...)

After that, the local infrastructure is ready to be attached to the VPN layer 2 tunnel.

This is achieved by enabling the TAP interface ("up"), creating VLAN interfaces on the TAP adapter (e.g. 'tap0.100', 'tap0.105', ...) and attaching them to the respective bridge.

## Use cases

* Connecting the network infrastructure of two geographically, WAN-separated sites while allowing members of the network to opperate on the same IP-subnets (that is, without routing)
* Quick remote access to a pre-existing network infrastructure (e.g. VMware vSphere port groups (based on VLANs)) with significantly less effort and potential configuration mistakes - compared to layer 3 VPN solutions
* Avoiding messy, hard to maintain ifup/ifdown tinc-up/tinc-down configuration scripts

## Dependencies
* python3
* iproute2
* bridge-utils
* vlan (including kernel module '8021q' in /etc/modules)

Successfully tested on Ubuntu 16.04 and Debian 9 with [Tinc VPN](https://www.tinc-vpn.org).


## Illustration

```
                              (TINC VPN / OpenVPN)
 -------- SITE 1 -------                                -------- SITE 2 -------
 eth1.100 <-> trunk0.100 <--\   ################   /--> trunk0.100 <-> eth1.100
 eth1.105 <-> trunk0.105 <--->> ---TAP-TUNNEL--- <<---> trunk0.105 <-> eth1.105
 eth1.110 <-> trunk0.110 <--/   ################   \--> trunk0.110 <-> eth1.110

 Hint: Interface names (ethernet adapter, bridge name, ...)
 do not neccesarily have to be identical among sites.

```

## Command line arguments

```
./trunk-tap.py --help
usage: trunk-tap.py [-h] [-start] [-stop] [-i TRUNK_INTERFACE]
                    [-t TAP_INTERFACE] [-v VLAN_DIR] [-b BRIDGE_NAME]
                    [--no-tap]

optional arguments:
  -h, --help            show this help message and exit
  -start                Creates all interfaces and establishes VLAN bridges
  -stop                 Reverses -start: Removes the previously created
                        interfaces
  -i TRUNK_INTERFACE, --interface TRUNK_INTERFACE
                        Specify the trunk interface on the host that will
                        provide the VLANs to the network (e.g. eth1)
  -t TAP_INTERFACE, --tap-interface TAP_INTERFACE
                        Specify the TAP interface on the host that will be
                        used by TINC/OpenVPN (e.g. $INTERFACE, tap0)
  -v VLAN_DIR, --vlan-dir VLAN_DIR
                        The path to the folder that contains the files that
                        represent the VLANs that will be created. - Default:
                        ./vlans/
  -b BRIDGE_NAME, --bridge BRIDGE_NAME
                        Name of the bridge that will be created. (e.g. trunk0,
                        br0)
  --no-tap              Only for special use: If used, the VLANs will be
                        created locally (e.g. trunk0.105 <-> eth1.105), but
                        the TAP interface won't be used.

```

## License
This script is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
