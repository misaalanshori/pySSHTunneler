import json
from pprint import pprint
import os, time
import threading

with open("tunnels.json", "r") as text:
    jsonConfig = json.loads(text.read())
baseCommand = 'autossh -M 0 -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" -o StrictHostKeyChecking=accept-new'
serverSideCMD = '"while true;do echo \$(sudo lsof -i | grep sshd); sleep 5; done"'
extraArgs = "-4"

threadKill = False

def generateCommand(serverInfo):
    tunnelFormat = "{}:{}:{}:{}"
    fullCommand = baseCommand + " -i " + serverInfo["sshKey"] + " " + extraArgs
    for tunnelL in serverInfo["tunnels"]["localTunnel"]:
        tunnel = serverInfo["tunnels"]["localTunnel"][tunnelL]
        fullCommand += " -L " + '"' + tunnelFormat.format(tunnel["localAddress"], tunnel["localPort"], tunnel["remoteAddress"], tunnel["remotePort"]) + '"'
    for tunnelR in serverInfo["tunnels"]["remoteTunnel"]:
        tunnel = serverInfo["tunnels"]["remoteTunnel"][tunnelR]
        fullCommand += " -R " + '"' + tunnelFormat.format(tunnel["remoteAddress"], tunnel["remotePort"], tunnel["localAddress"], tunnel["localPort"]) + '"'
    fullCommand += " {}@{} -p{}".format(serverInfo["username"], serverInfo["address"], serverInfo["port"])
    return fullCommand

def process():
    commands = {}
    for i in jsonConfig["servers"]:
        commands[i] = (generateCommand(jsonConfig["servers"][i]))
    return commands

def sshAccess(tname, sshCmd):
    print("Connecting to {}".format(tname))
    # print(sshCmd)
    ssh = os.popen(sshCmd + " " + serverSideCMD)
    
    print("Waiting for {}".format(tname))
    while not threadKill and (ssh._proc.poll() is None):
        time.sleep(10)
        sshLine = ssh.readline().split("sshd ")
        print(sshLine)
        print("="*24)
        sshdData = []
        for i in sshLine:
            sshdData.append(i.split(" "))
        print("\n")            
        print(" {} ".format(tname).center(24, "="))
        for i in sshdData:
            if len(i) < 10:
                continue
            print("{}: {} ({}, {}, {})".format(tname, i[-3], i[1], i[-4], i[-2][1:-1]))
        print("="*24)
        print("\n")
    if ssh._proc.poll() is not None:
        print("SSH Process for {} was killed, restarting".format(tname))
        sshAccess(tname, sshCmd)

def main():
    data = process()
    threads = []
    for i in data:
        threads.append(threading.Thread(target=sshAccess, args=(i,data[i],)))
    for i in threads:
        i.start()
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        threadKill = True
        exit()