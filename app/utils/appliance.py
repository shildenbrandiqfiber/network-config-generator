"""
utility function for the appliance
"""
import socket
import subprocess

import psutil
import redis


def verify_appliance_status():
    """
    simple verification method for the services on the appliance
    :return:
    """
    result = {
        "ftp": False,
        "tftp": False,
        "redis": False,
        "celery_worker": False
    }

    # assume that the setup script was running on the server, if the ports are open, TFTP and FTP should be available
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.type == socket.SOCK_DGRAM and conn.laddr.port == 69:
                result["tftp"] = True

            elif conn.type == socket.SOCK_STREAM and conn.status == psutil.CONN_LISTEN and conn.laddr.port == 21:
                result["ftp"] = True

    except psutil.AccessDenied:
        # listing the sockets requires root privileges on macOS (not on Linux)
        pass

    # we assume that the redis server is running locally, therefore we can use the CLI to test the connection
    rs = redis.Redis("localhost")
    try:
        if rs.ping():
            result["redis"] = True

    except:
        # ignore silently
        result["redis"] = False

    # to verify the state of the celery worker threads, we look at the processes
    output = subprocess.check_output(["ps", "ax"]).decode("utf-8")
    if ("celery" in output) and ("-A app.celery" in output):
        result["celery_worker"] = True

    return result


def get_local_ip_addresses():
    """
    returns a dictionary that contains the interface names and the associated IPv4 addresses
    :return:
    """
    result = {}
    for intf, addresses in psutil.net_if_addrs().items():
        ipv4_addresses = [a.address for a in addresses if a.family == socket.AF_INET and a.address != "127.0.0.1"]
        if ipv4_addresses:
            result[intf] = ipv4_addresses

    return result
