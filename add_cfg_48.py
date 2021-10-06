import sys
neighbor_cfg_file = "C:\\huawei\\neighbor.txt"
default_cfg_file = "default_cfg_48.txt"
file_result = "C:\\huawei\\vrpcfg.cfg"

# -------------------------------------
def read_cfg_from_file(file):
    lst = []
    f = open(file)
    for line in f:
        lst.append(line)
    f.close()
    return lst
# -------------------------------------

def write_vrpcfg(file, result):
    f = open(file, 'w')
    f.writelines(result)
    f.close()
    return 0

def parse_nbr_cfg(nb_cfg):
    start_vlan_description = -1
    end_vlan_description = -1
    start_gig1 = -1
    end_gig1 = -1
    vlan_batch = []
    i = 0
    temp = 1
    vlan1_start_check = 0
    vlan1_end_check = 0
    gig1_start_check = 0
    gig1_end_check = 0
    for line in nb_cfg:
        if line.find("vlan batch") != -1:
            vlan_batch.append(line)
        if line.find("interface Vlanif") != -1:
            vlanif = line
        if line.find("ip route-static ") != -1:
            route = line
        if vlan1_start_check == 0:
            if line.find("vlan 1") != -1:
                start_vlan_description = i
                vlan1_start_check = 1
        if vlan1_start_check == 1 and vlan1_end_check == 0:
            if line.find("#") != -1:
                end_vlan_description = i
                vlan1_end_check = 1
        if gig1_start_check == 0 and temp == 1:
            if line.find("interface GigabitEthernet0/0/1") != -1:
                start_gig1 = i
                gig1_start_check = 1
        if gig1_start_check == 1 and gig1_end_check == 0:
            if line.find("#") != -1:
                end_gig1 = i
                gig1_end_check = 1
        if line.find("#") != -1:
            temp = 1
        else:
            temp = 0
        i += 1
    uplinks = nb_cfg[start_gig1:end_gig1+1]
    vlan_decription = nb_cfg[start_vlan_description:end_vlan_description]
    result = []
    result.append(vlan_batch)
    result.append(vlanif)
    result.append(vlan_decription)
    result.append(uplinks)
    result.append(route)
    return result

# -------------------------------------
def get_acl(ip):
    return ip[0:ip.rfind('.') + 1] + "0"
# -------------------------------------
def pppoe_inject(cfg_vlans, vlan_pppoe):
    i = 0
    position_main_vlan = -1
    position_old_vlan = -1
    res_main_vlan = "vlan " + str(vlan_pppoe) + "\n"
    for line in cfg_vlans:
        if line.find("multicast-vlan user-vlan") != -1:
            cfg_vlans[i] = " multicast-vlan user-vlan 1 " + str(vlan_pppoe) + "\n"
            temp = line.split()
            old_pppoe_vlan = temp[len(temp)-1]
        if line.find("description INTERNET-MAIN") != -1:
            position_main_vlan = i - 1
        if line.find("dhcp snooping trusted interface GigabitEthernet0/0/2") != -1:
            cfg_vlans.insert(i + 1, " dhcp snooping trusted interface GigabitEthernet0/0/3\n")
            cfg_vlans.insert(i + 2, " dhcp snooping trusted interface GigabitEthernet0/0/4\n")
        if line.find(res_main_vlan) != -1:
            position_old_vlan = i
        i += 1
    cfg_vlans[position_main_vlan] = res_main_vlan
    cfg_vlans[position_old_vlan] = "vlan " + old_pppoe_vlan + "\n"
    return cfg_vlans
# -------------------------------------
def write_vrpcfg(file, result):
    f = open(file, 'w')
    f.writelines(result)
    f.close()
    return 0
# -------------------------------------
neighbor_cfg = read_cfg_from_file(neighbor_cfg_file)
default_cfg = read_cfg_from_file(default_cfg_file)

changes = parse_nbr_cfg(neighbor_cfg)

position_sysname = 2
position_acl = 35
position_ip = 99
position_route = 540
position_location = 554
position_vlanif = 97
position_vlan_batch = 10
position_vlan_description = 60
position_uplink = 536

result_cfg = default_cfg


#sw_sysname = sys.argv[1]
#sw_ip = sys.argv[2]
#sw_main_vlan = sys.argv[3]
#sw_location = sys.argv[4]

#neighbor_name = sys.argv[4]
#sw_sysname = "her"
#sw_ip = "192.168.123.14"
#sw_location = "Efremova 7771"
#sw_main_vlan = 3110

sw_sysname = input("sysname :")
sw_ip = input("ip :")
sw_location = input("location: ")
sw_main_vlan = input("main vlan: ")


#" bpdu enable"
#" qos pq"

result_cfg[position_sysname] = " sysname sw-ud" + sw_sysname + "\n"
result_cfg[position_ip] = " ip address " + sw_ip + " 255.255.255.224" + "\n"
result_cfg[position_location] = " snmp-agent sys-info location " + sw_location + "\n"
result_cfg[position_acl] = " rule 20 permit source " + get_acl(sw_ip) + " 0.0.1.255" + "\n"
result_cfg[position_vlanif] = changes[1]
result_cfg[position_route] = changes[4]



vlan_batch = list(changes[0])
vlan_description = list(changes[2])
vlan_description = pppoe_inject(vlan_description, sw_main_vlan)
uplink1 = list(changes[3])
uplink1.insert(-1, " bpdu enable\n")
uplink1.insert(-1, " qos pq\n")
uplink2 = uplink1.copy()
uplink2[0] = "interface GigabitEthernet0/0/2\n"
#uplink2.insert(, "interface GigabitEthernet0/0/2\n")
#for line in uplink1:
uplink3 = uplink1.copy()
uplink3[0] = "interface GigabitEthernet0/0/3\n"
uplink4 = uplink1.copy()
uplink4[0] = "interface GigabitEthernet0/0/4\n"
uplinks = uplink1 + uplink2 + uplink3 + uplink4




result_cfg = default_cfg[0:position_vlan_batch] + vlan_batch + \
             default_cfg[position_vlan_batch+1:position_vlan_description+1] + vlan_description +\
             default_cfg[position_vlan_description+1:position_uplink+1] + uplinks + \
             default_cfg[position_uplink+2:len(default_cfg)]





#for line in result_cfg:
#    print(line)
write_vrpcfg(file_result,result_cfg)

