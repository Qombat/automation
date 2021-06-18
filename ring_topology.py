import csv
import ipaddress
import sys
import telnetlib
import re
from graphviz import Digraph

'''
Задача: Имеется csv файл, в котором представлен список всех коммутаторов в сети.
Необходимо нарисовать топологию одного кольца, в котором визуализируются связи с соедними коммутаторами.
IP адреса коммутаторов имеют маску /27.
'''
'''
Из файла switches.csv необходимо по вводу sysname найти ip адрес коммутатора
'''
with open('switches.csv', newline='') as f:
    reader = csv.DictReader(f, delimiter=',')
    ud = input('sysname: ')
    for row in reader:
        if ud in row['sysname']:
            ip_ud = row['ip_address']
'''
Необходимо рассчитать все возможные адреса в кольце
'''
ip = ip_ud + '/27'
ip = str(ip)
b = str(ipaddress.ip_interface(ip).network)
a = b.index('/')
ip_network = b[0:a - len(b)]
a = ip_network[0:ip.rfind('.') + 1]
pos_point =len(a)
start_ip = int(ip_network[pos_point:len(ip_network)]) + 2
ip_pool = []
for i in range(start_ip, start_ip+29):
    ip_pool.append(a[0:pos_point] + str(i))

telnet_pool = []

user = "admin"
password = "***"
commands = ['dis ll n b\r\n','screen-length 0 temporary\r\n']
count_up = 0
count_down = 0
neighbors = {}
neig = {}
ng = {}
appendix = []
pool = {}

'''
Из пула рассчитанных адресов необходимо извлечь только те адреса, которые имеются в файле switches.csv
Далее пройтись по каждому адресу по телнет, выяснить какие у него имеются соседи и на каких портах
'''

with open('switches.csv', newline='') as f:
    reader = csv.DictReader(f, delimiter=',')
    for row in reader:
        if row['ip_address'] in ip_pool:
            telnet_pool.append(row['ip_address'])
            HOST = row['ip_address']
            try:
                sys_loc = {row['sysname'] : row['location']}
                pool.update(sys_loc)
                commands = ['dis ll n b\r\n','screen-length 0 temporary\r\n']
                connect = telnetlib.Telnet(HOST,23,3)                
                #print(row['sysname'], row['ip_address'])
                connect.write((user+"\r\n").encode('ascii'))
                connect.write((password + "\r\n").encode('ascii'))
                a = connect.read_until('>'.encode('ascii'), timeout=2)
                for line in commands:
                    connect.write((line).encode('ascii'))
                connect.write(("\r\n").encode('ascii'))
                tlnt_lldp = connect.read_until(b'only.', timeout=2)
                #print(tlnt_lldp.decode('ascii'))
                tlnt_lldp = tlnt_lldp.decode('cp1251')
                tlnt_lldp = re.split(r'\r\n', tlnt_lldp)
                sys = row['sysname']
                lldp = {}
                for line in tlnt_lldp:
                    port = None
                    ll_sys = None
                    ll_port = None
                    port = re.search(r'^GE\S+', line)
                    if port != None:
                        port = str(port.group())
                    if port == None:
                        port = re.search(r'Eth\S+', line)
                        if port != None:
                            port = str(port.group())
                    ll_sys = re.search(r'sw-ud\S+', line)
                    if ll_sys != None:
                        ll_sys = str(ll_sys.group())
                    if ll_sys == None:
                        ll_sys = re.search(r'GW\S+', line)
                        if ll_sys != None:
                            ll_sys = str(ll_sys.group())
                    ll_port = re.search(r'\sGE\S+', line)
                    if ll_port != None:
                        ll_port = str(ll_port.group())
                    if ll_port == None:
                        ll_port = re.search(r'\sEth\S+', line)
                        if ll_port != None:
                            ll_port = str(ll_port.group())
                    if (port != None) and ll_sys != None and ll_port != None:
                        neighbor = {port : {ll_sys : ll_port}}
                        lldp.update(neighbor)
                    port = None
                    ll_sys = None
                    ll_port = None
                neighbors[sys] = lldp
                connect.close()
                count_up = count_up + 1
            except:
                count_down = count_down + 1

print('\nВ сети: ', count_up, ' / Не в сети: ', count_down)

'''
Необходимо визуализировать полученные данные
'''

dot = Digraph()
dot.attr(rankdir = "LR")
dot.attr(fontcolor='white')
lldp = neighbors
link = []

'''
Первым должен отобразиться квартальный коммутатор, но доступа к нему не имеется,
поэтому необходимо выявить его исодя из информации по его соседним коммутаторам
'''
for key in lldp:
    edge1 = edge2 = edge3 = edge4 = 0
    lldp2 = lldp.get(key)
    edge1 = key
    for key in lldp2:
        lldp3 = lldp2.get(key)
        edge2 = key
        for key in lldp3:
            edge3 = key
            if 'GW' in str(edge3):
                dot.node(edge3, shape='record', label=edge3, height='5', color='#006699', fillcolor='#006699', fontcolor='white', style='filled')
                break
'''
Далее отображаем связи между коммутаторами
'''
for key in lldp:
    edge1 = edge2 = edge3 = edge4 =  0
    lldp2 = lldp.get(key)
    edge1 = key
    location = pool.get(edge1)
    sys_locat = edge1 + '\\n' + location
    print(sys_locat)
    for key in lldp2:
        lldp3 = lldp2.get(key)
        edge2 = key
        for key in lldp3:
            lldp4 = lldp3.setdefault(key)
            edge3 = key
            edge4 = lldp4
            print(edge1, edge2, edge3, edge4)
            dot.node(edge1, shape='record', style='filled')
            link.append(edge1)
            dot.node(edge1, label=sys_locat)
            if (edge3 not in link):
                dot.edge(edge1, edge3, label="     ", headlabel=edge4, taillabel=edge2, fontname='Courier', fontsize='8', style='dashed', arrowhead='none')
            dot.edge(edge3, edge1, arrowhead='none', color='transparent')
print(dot.source) 

dot.render('MAP', view=True)
dot.save('MAP.dot')
