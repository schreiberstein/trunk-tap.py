# trunk-tap.py
A clean and efficient way to transport VLANs over a TINC/OpenVPN TAP-interface.


## Introduction
trunk-tap.py is a Linux command line utility to connects a set of 802.1Q VLANs to a TINC VPN/OpenVPN TAP-interface
and is designed to be invoked by ifup/ifdown scripts after starting or stopping a VPN connection.

It reads the filenames from the content of a folder containing files corresponding to the VLAN ID (e.g. '100', '105', ...),
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


## Illustration (Logical)

```
                              (TINC VPN / OpenVPN)
 -------- SITE 1 -------                                -------- SITE 2 -------
 eth1.100 <-> trunk0.100 <--\   ################   /--> trunk0.100 <-> eth1.100
 eth1.105 <-> trunk0.105 <--->> ---TAP-TUNNEL--- <<---> trunk0.105 <-> eth1.105
 eth1.110 <-> trunk0.110 <--/   ################   \--> trunk0.110 <-> eth1.110

 Hint: Interface names (ethernet adapter, bridge name, ...)
 do not neccesarily have to be identical among sites.

```

## Illustration (Physical)

```
                                    
   [----------------------------------------------- SITE 1 ---------------------------]                           [------- SITE 2 -----]

   [---- HARDWARE ----][-------------------------- SOFTWARE --------------------------][-------- HARDWARE --------]

                      ||    /--> eth1.100 <-> trunk0.100 <--\   ################      ||      #/#/#/#/#/#/#/#/  |/|
   Local Network <-> eth1 <<---> eth1.105 <-> trunk0.105 <--->> ---TAP-TUNNEL--- ==> eth0 ==>  ---INTERNET---   |/|    Same for SITE 2
                      ||    \--> eth1.110 <-> trunk0.110 <--/   ################      ||      #\#\#\#\#\#\#\#\  |/|  (mirrored/reversed)

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

## Sample configuration - TINC VPN

Hint: Connection name is "myremote" in this example.
'eth1' is the ethernet interface that will be used as trunk port.
'remotebr' is the name for the bridge interfaces that will be created by the script.
"/etc/tinc/myremote/vlans/" is the path of the folders that contain the empty files representing the VLANs to add.
The "$INTERFACE" is a variable for the TAP interface (here: "myremote" created by tinc) that is made available in the tinc-up or tinc-down scripts.
It may be entered manually (tap0, nameofyourtincconnection, ...).


Configuration files for TINC connection "myremote" are located in : /etc/tinc/myremote/

* Create a regular TINC connection - in a "Mode=Switch" configuration
* Copy "trunk-tap.py" into the "/etc/tinc/myremote/" folder, make it executable (chmod +x)
* Create a new "tinc-up" file with the following contents and make it executable as well

```
#!/bin/bash
/etc/tinc/myremote/trunk-tap.py -start -i eth1 -b remotebr -v=/etc/tinc/myremote/vlans/ -t $INTERFACE
```
* Create a new "tinc-down" file with the following contents and make it executable as well

```
#!/bin/bash
/etc/tinc/myremote/trunk-tap.py -stop -i eth1 -b remotebr -v=/etc/tinc/myremote/vlans/ -t $INTERFACE
```

* Create a folder called /etc/tinc/myremote/vlans
* Create empty files for the VLAN IDs of your desired networks

```
root@linux:/etc/tinc/myremote/vlans# touch 100 105 110 800 850 1015
root@linux:/etc/tinc/myremote/vlans# ls
100  105  110  800  850  1015
```

* Do the same on the host that you wish to connect your VLANs to
* Test your connection (e.g. "tincd -d 5 -D -n myremote" in a GNU screen session)
* Attach a VLAN capable machine to your trunk port, create a connection on a VLAN, try to ping to the 'remote' network

The "ip a" connection list and bridge status would look like this (excerpt for VLAN ID 100):
```
root@linux:/etc/tinc# ip a
...
3: eth1.100@eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master remotebr state UP group default qlen 1000
    link/ether xx:xx:xx:xx:xx:xx brd ff:ff:ff:ff:ff:ff
    inet6 fe80::xxx:xxxx:xxxx:xxxx/64 scope link
       valid_lft forever preferred_lft forever

4: myremote.100: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UNKNOWN group default qlen 1000
    link/ether xx:xx::xx:xx:xx brd ff:ff:ff:ff:ff:ff
    inet6 fe80::xxxx:xxxx:xxx:xxxx/64 scope link 
       valid_lft forever preferred_lft forever

5: remotebr.100: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
    link/ether xx:xx:xx:xx:xx:xx brd ff:ff:ff:ff:ff:ff
    inet6 fe80::xxxx:xxxx:xxxx:xxx/64 scope link 
       valid_lft forever preferred_lft forever


root@linux:/etc/tinc# brctl show
bridge name	bridge id		STP enabled	interfaces
remotebr.100		8000.000000000	no		eth1.100
                                                        myremote.100

```
Upon termination of the VPN connection, trunk-tap.py will remove all adapters that were previously created by it.


## License
This script is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
