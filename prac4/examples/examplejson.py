import json

with open("C:\\Users\\Alisherka\\Desktop\\сабак\\PP2\\prac4\\examples\\sample-data.json", "r") as f:
    data = json.load(f)

print("Interface Status")
print("================================================================================")
print('DN', '                                                 ', 'Description', '           ', 'Speed','    ', 'MTU')
print("-------------------------------------------------- --------------------  ------  ------")

for item in data["imdata"]:
    attributes = item["l1PhysIf"]["attributes"]
    
    dn = attributes["dn"]
    descr = attributes["descr"]
    speed = attributes["speed"]
    mtu = attributes["mtu"]
    
    if dn == "topology/pod-1/node-201/sys/phys-[eth1/33]" or dn == "topology/pod-1/node-201/sys/phys-[eth1/34]" or dn == "topology/pod-1/node-201/sys/phys-[eth1/35]":
        print(f"{dn:60} {descr:15} {speed:10} {mtu}")