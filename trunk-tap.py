#!/usr/bin/env python3

# < trunk-tap.py >
# Version 1.0 < 20171022 > 
# Copyright 2017: Alexander Schreiber < schreiberstein[at]gmail.com >
# https://github.com/schreiberstein/trunk-tap.py

# MIT License:
# ============
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# See: https://opensource.org/licenses/MIT


# Introduction:
# =============
# trunk-tap.py is a Linux command line utility to connects a set of 802.1Q VLANs to a TINC VPN/OpenVPN TAP-interface and is designed to be invoked by ifup/ifdown scripts after starting or stopping a VPN connection.
# Dependencies (on Debian): python3, iproute2, bridge-utils, vlan (including kernel module '8021q' in /etc/modules)
# It reads the filenames from the content of folder containing files corresponding to the VLAN ID (e.g. '100', '105', ...), then creates VLAN interfaces on a local Ethernet adapter used as "trunk port" (e.g. 'eth1.100', 'eth1.105', ...).
# The script then proceeds to generate bridge interfaces for every VLAN ID. (e.g. "trunk0.100", "trunk0.105", ...) and attaches the respective Ethernet VLAN interfaces to the bridge. (e.g. 'trunk0.105 <-> eth1.105', ...)
# After that, the local infrastructure is ready to be attached to the VPN layer 2 tunnel.
# This is achieved by enabling the TAP interface ("up"), creating VLAN interfaces on the TAP adapter (e.g. 'tap0.100', 'tap0.105', ...) and attaching them to the respective bridge.

# Illustration:
# =============

#                              (TINC VPN / OpenVPN)
# -------- SITE 1 -------                                -------- SITE 2 -------
# eth1.100 <-> trunk0.100 <--\   ################   /--> trunk0.100 <-> eth1.100
# eth1.105 <-> trunk0.105 <--->> ---TAP-TUNNEL--- <<---> trunk0.105 <-> eth1.105
# eth1.110 <-> trunk0.110 <--/   ################   \--> trunk0.110 <-> eth1.110

# Hint: Interface names (ethernet adapter, bridge name, ...) do not neccesarily have to be identical among sites.


# --------------------------------------------------------------------------------------------------------------- #

# Code:
# =====

# Import required Python3 modules
import os, sys, subprocess
from pathlib import Path


# Create VLAN-interfaces on trunk interface (e.g. 'eth1.100', 'eth1.105', ...)
def trunk_vlan_add():

    # Initialize our trunk interface, if it is not up yet
    p = subprocess.Popen("ip link set dev " + trunk_interface + " up", shell=True)
    p.communicate()

    # Create VLAN interfaces on trunk_interface
    for filename in os.listdir(vlan_dir):
        p = subprocess.Popen("ip link add link " + trunk_interface + " name " + trunk_interface + "." + filename + " type vlan id " + filename +" ; " + "ip link set " + trunk_interface + "." + filename + " up", shell=True)
        p.communicate()
        continue
    return

# Function to remove VLAN interfaces from trunk interface
def trunk_vlan_del():

    # Remove VLAN interfaces on trunk_interface
    for filename in os.listdir(vlan_dir):
        p = subprocess.Popen("ip link set dev " + trunk_interface + "." + filename + " down" + " ; " + "ip link delete " + trunk_interface + "." + filename, shell=True)
        p.communicate()
        continue
    return

# Function to create main bridge (no VLAN ID - May be used to attach a VLAN/network to provide network to devices without VLAN support (VLAN0 - untagged))
def bridge_add():
    p = subprocess.Popen("ip link add name " + bridge_name + " type bridge" + " ; " + "ip link set " + bridge_name + " up" + " ; " + "ip link set " + trunk_interface + " master " + bridge_name, shell=True)
    p.communicate()
    return

# Function to remove bridge
def bridge_del():
    p = subprocess.Popen("ip link set " + bridge_name + " down" + " ; " + "ip link delete " + bridge_name + " type bridge", shell=True)
    p.communicate()
    return

# Creates bridges to be used for VLAN bridging (e.g. 'trunk0.100', 'trunk0.105', ..) - illustration: eth1.105 <-> Bridge: trunk0.105 <-> tap0.105
def bridge_vlan_add():
    for filename in os.listdir(vlan_dir):
        p = subprocess.Popen("ip link add name " + bridge_name + "." + filename + " type bridge" + " ; " + "ip link set " + bridge_name + "." + filename + " up", shell=True)
        p.communicate()
        continue
    return

# Function to remove VLAN interfaces from the bridge
def bridge_vlan_del():
    for filename in os.listdir(vlan_dir):
        p = subprocess.Popen("ip link set dev " + bridge_name + "." + filename + " down" + " ; " + "ip link delete " + bridge_name + "." + filename, shell=True)
        p.communicate()
        continue
    return


# Function to bridge the VLANs of the physical interface with the VLANs of the bridge
def bridge():
    for filename in os.listdir(vlan_dir):
        p = subprocess.Popen("ip link set " + trunk_interface + "." + filename + " master " + bridge_name + "." + filename, shell=True)
        p.communicate()
        continue
    return

# Create VLAN-interfaces on tap interface
def tap_vlan_add():

    # Initialize the tap interface, if it is not up yet
    p = subprocess.Popen("ip link set dev " + tap_interface + " up", shell=True)
    p.communicate()

    # Create VLAN interfaces on tap interface
    for filename in os.listdir(vlan_dir):
        p = subprocess.Popen("ip link add link " + tap_interface + " name " + tap_interface + "." + filename + " type vlan id " + filename + " ; " + "ip link set dev " + tap_interface + "." + filename + " up", shell=True)
        p.communicate()
        continue
    return


# Function to bridge the VLANs of the physical interface with the VLANs of the bridge
def tap_bridge():
    for filename in os.listdir(vlan_dir):
        p = subprocess.Popen("ip link set " + tap_interface + "." + filename + " master " + bridge_name + "." + filename, shell=True)
        p.communicate()
        continue
    return

# Function to enable ("up") the tap interface
def tap_if_up():
    p = subprocess.Popen("ip link set dev " + tap_interface + " down", shell=True)
    p.communicate();
    return

# Function to disable ("down") the tap interface
def tap_if_down():
    p = subprocess.Popen("ip link set dev " + tap_interface + " down", shell=True)
    p.communicate();
    return


# Function to remove VLAN interfaces from tap interface
def tap_vlan_del():

    # Remove VLAN interfaces on tinc_interface
    for filename in os.listdir(vlan_dir):
        p = subprocess.Popen("ip link set dev " + tap_interface + "." + filename + " down" + " ; " + "ip link delete " + tap_interface + "." + filename, shell=True)
        p.communicate()
        continue
    return


# Function to remove members attached by the tap_bridge() function
def tap_unbridge():
    for filename in os.listdir(vlan_dir):
        p = subprocess.Popen("ip link set " + tap_interface + "." + filename + " nomaster", shell=True)
        p.communicate()
        continue
    return


# Function to remove members attached by the bridge() function
def unbridge():
    for filename in os.listdir(vlan_dir):
        p = subprocess.Popen("ip link set " + trunk_interface + "." + filename + " nomaster", shell=True)
        p.communicate()
        continue
    return

# ------------------------
# Note: Order of execution
# ------------------------

# Start:
# ------
# trunk_vlan_add()
# bridge_add()
# bridge_vlan_add()
# bridge()
# tap_if_up()
# tap_vlan_add()
# tap_bridge()

# Stop:
# -----
# tap_unbridge()
# tap_vlan_del()
# tap_if_down()
# unbridge()
# bridge_vlan_del()
# bridge_del()
# trunk_vlan_del()


# Start function - Used to execute all other functions
def start(no_tap):
    trunk_vlan_add()
    bridge_add()
    bridge_vlan_add()
    bridge()
    # Don't do anything with the TAP interface if --no_tap was specified
    if not no_tap:
        tap_if_up()
        tap_vlan_add()
        tap_bridge()
    return
    
# Stop function - reverses the actions performed by start()
def stop(no_tap):
    # Don't do anything with the TAP interface if --no_tap was specified 
    if not no_tap:
        tap_unbridge()
        tap_vlan_del()
        tap_if_down()

    unbridge()
    bridge_vlan_del()
    bridge_del()
    trunk_vlan_del()
    return


# # # # # # # # #
# Main function #
# # # # # # # # #


def main():
    # If no arguments are specified, quit.
    if len(sys.argv) == 1:
        print("Error: No arguments specified. Enter ./trunktap.py --help for more information.")
        quit()


    # If arguments are given, parse them and run script.
    import argparse
    parser = argparse.ArgumentParser()

    # Add arguments
    parser.add_argument("-start", dest="is_start", action="store_true", help="Creates all interfaces and establishes VLAN bridges")
    parser.add_argument("-stop", dest="is_stop", action="store_true", help="Reverses -start: Removes the previously created interfaces")
    parser.add_argument("-i", "--interface", dest="trunk_interface", help="Specify the trunk interface on the host that will provide the VLANs to the network (e.g. eth1)")
    parser.add_argument("-t", "--tap-interface", dest="tap_interface", help="Specify the TAP interface on the host that will be used by TINC/OpenVPN (e.g. $INTERFACE, tap0)")
    parser.add_argument("-v", "--vlan-dir", dest="vlan_dir", help="The path to the  folder that contains the files that represent the VLANs that will be created. - Default: ./vlans/ ", default="./vlans/")
    parser.add_argument("-b", "--bridge", dest="bridge_name", help="Name of the bridge that will be created. (e.g. trunk0, br0)")
    parser.add_argument("--no-tap", dest="no_tap", help="Only for special use: If used, the VLANs will be created locally (e.g. trunk0.105 <-> eth1.105), but the TAP interface won't be used.", default=False, action="store_true")

    
    # Parse arguments
    arguments = parser.parse_args()

    # Create local variables because the functions use these
    global trunk_interface, tap_interface, vlan_dir, bridge_name
    trunk_interface = arguments.trunk_interface
    tap_interface = arguments.tap_interface
    vlan_dir = arguments.vlan_dir
    bridge_name = arguments.bridge_name

    
    # Make sure that either start or stop was specified (NOT XOR)
    if not arguments.is_start ^ arguments.is_stop:
        print("Error: You have to specify either -start or -stop. Only one option is valid.")
        quit()
    

    # Make sure that arguments are not empty
    if not (trunk_interface and tap_interface and vlan_dir and bridge_name):
        print("Error: You have to specify -i, -t, -b and -v.")
        quit()

    # Execute either function start() or stop() and pass the no_tap-variable
    if arguments.is_start:
        start(arguments.no_tap)

    if arguments.is_stop:
        stop(arguments.no_tap)
    
    quit()

# Only run main if the script is explicitly executed (e.g. './trunktap.py')
if __name__ == "__main__":
    main()
