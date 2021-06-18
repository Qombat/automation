import sys
import telnetlib
import ipaddress
import re
'''
Есть необходимость автоматизировать процесс прописывания определенного влана в кольце
На сети используются коммутаторы Quidway s2300
IP адреса для управления коммутаторами в маске /27
'''
ip = input('Введите ip адрес и маску: ')
vlan_id = input('Введите номер влана: ')
vlan_descr = input('Введите описание влана: ')

user = "admin"
password = "***"

save = ['q','q','save','y','screen-length 0 temporary']

count = 0
count_ud = 0

'''
Необходимо рассчитать пул IP адресов в список
'''
b = str(ipaddress.ip_interface(ip).network)
a = b.index('/')
ip_network = b[0:a - len(b)]
a = ip_network[0:ip.rfind('.') + 1]
pos_point =len(a)
start_ip = int(ip_network[pos_point:len(ip_network)]) + 2
ip_pool = []

for i in range(start_ip, start_ip+29):
    ip_pool.append(a[0:pos_point] + str(i))

'''
Далее обращаемся к каждому адресу из списка, если есть ответ, то выясняем порты, на которых иммется сосед (другой коммутатор)
И на этих портах прописываем влан тегом
'''
for line in ip_pool:
    HOST = line
    try:
        commands = ['sys','vlan ','descr ']
        commands[1] = 'vlan ' + vlan_id
        commands[2] = 'descr ' + vlan_descr
        print('___________')
        connect = telnetlib.Telnet(HOST,23,5)
        connect.write((user+"\r\n").encode('ascii'))
        connect.write((password + "\r\n").encode('ascii'))
        connect.write(('dis ll n b\r\n').encode('ascii'))
        connect.write(('screen-length 0 temporary\r\n').encode('ascii'))
        tlnt = connect.read_until(b'only.')
        tlnt = tlnt.decode('cp1251')
        tlnt = re.split(r'\r\n', tlnt)
        for line in tlnt:
            port = '0'
            ll_sys = '0'
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
            if (port != None) and ll_sys != None:
                if 'Eth' in port:
                    port_id = re.search(r'0/0/\S+', port)
                    port_id = str(port_id.group())
                    commands.append('int ethe' + port_id)
                    commands.append('port hyb tag vlan ' + vlan_id)          
                if 'GE' in port:
                    port_id = re.search(r'0/0/\S+', port)
                    port_id = str(port_id.group())
                    commands.append('int gig' + port_id)
                    commands.append('port hyb tag vlan ' + vlan_id)
        commands.extend(save)
        for line in commands:
            connect.write((line + "\r\n").encode('ascii'))
        out_tlnt = connect.read_until(b'only.', timeout = 3)
        print(out_tlnt.decode('ascii'))
        count_ud = count_ud + 1
        connect.close()
        commands = []
    except:
'''
Если нет ответа более 10 адресов, то выходим из цикла
'''
        if count < 10:
            print(line, "Не в сети")
            count = count + 1
        elif count == 10:
            break
count_ud = str(count_ud)
print("___________\nКоличество прописанных коммутаторов в кольце: " + count_ud)  
input()
