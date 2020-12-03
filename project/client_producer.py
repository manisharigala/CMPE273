import zmq
import time
import sys
from itertools import cycle
import consul
from bisect import bisect

SERVER_PORT = 0
producers = {}
def create_clients(servers):
    global producers 
    context = zmq.Context()
    for server in servers:
        print(f"Creating a server connection to {server}...")
        producer_conn = context.socket(zmq.PUSH)
        producer_conn.bind(server)
        producers[server] = producer_conn
    return producers

def create_one_client(server):
    global producers 
    context = zmq.Context()
    print(server)
    print(f"Creating a server connection to {server}...")
    producer_conn = context.socket(zmq.PUSH)
    producer_conn.bind(server)
    producers[server] = producer_conn
    return producers

# -----------------------------------------------------------------------------------------

def generate_data_round_robin(servers):
    print("Starting...Round Robin")
    producers = create_clients(servers)
    pool = cycle(producers.values())
    for num in range(10):
        data = { 'op' : 'PUT','key': f'key-{num}', 'value': f'value-{num}' }
        print(f"Sending data:{data}")
        next(pool).send_json(data)
        time.sleep(1)
    print("Done")

# ------------------------------------------------------------------------------------------------

def to_int(string):
    res = ""
    for char in string:
        res += str(ord(char))
    return int(res) 

def hash_func(x):
    a = 12345
    b = 123
    return (a*x + b) % 360 

def add_node():
    
    global producers
    context = zmq.Context()
    consumer = context.socket(zmq.PULL)
    consumer.bind(f"tcp://127.0.0.1:3000")

    con_servers = list(c.agent.services().keys())
    servers = ["tcp://"+server for server in con_servers]

    bins_angle_to_name = dict()
    bin_angle_list = []
    for s in servers:
        bins_angle_to_name[hash_func(to_int(s))] = s 
        bin_angle_list.append(hash_func(to_int(s)))
    
    #sort bin_angle_list
    bin_angle_list.sort()
    new_node_angle = hash_func(to_int("tcp://127.0.0.1:200{SERVER_PORT}"))
 
    # Finding new Node's position
    pos = bisect(bin_angle_list,new_node_angle)
    pos -= 1

    if pos == len(bin_angle_list):
        #node is first node
        node = bin_angle_list[0]
    else :
        node = bin_angle_list[pos]
        # node is the pos node

    # Getting old node's data
    json_string = {'op' : 'GET_ALL' }
    # print(producers)
    # print(producers[bins_angle_to_name[node]])
    # print(node)
    producers[bins_angle_to_name[node]].send_json(json_string)
    recv_json = consumer.recv_json()
    # print(recv_json)
    recv_json = recv_json['Collection']

    # Adding New Server
    global SERVER_PORT
    port = 2000 + SERVER_PORT
    c.agent.service.register(name=f"127.0.0.1:200{SERVER_PORT}", port = port)
    new_server = f'tcp://127.0.0.1:200{SERVER_PORT}'
    SERVER_PORT += 1
    # print(new_server)
    producers = create_one_client(new_server)
    

    # After adding new server

    con_servers = list(c.agent.services().keys())
    servers = ["tcp://"+server for server in con_servers]

    bins_angle_to_name = dict()
    bin_angle_list = []
    for s in servers:
        bins_angle_to_name[hash_func(to_int(s))] = s 
        bin_angle_list.append(hash_func(to_int(s)))
    
    bin_angle_list.sort()
    #producers = create_clients(servers)
    print("Rehashing")
    print(bin_angle_list)
    for data in recv_json:
        hashed_data = hash_func(to_int(data['key']))
        print("Key Hash value:", hashed_data)
        # get the consistent hashing node 
        # send it to the node
        angle = -1
        for i in bin_angle_list:
            if  i >= hashed_data:
                angle = i
                break
        data['op'] = 'PUT'
        if angle == -1:
            bin_to_be_hashed_to = bins_angle_to_name[bin_angle_list[0]]
            print("bin to be hashed to", bin_to_be_hashed_to)
        else:
            bin_to_be_hashed_to = bins_angle_to_name[angle]
            print("bin to be hashed to", bin_to_be_hashed_to)
        producers[bin_to_be_hashed_to].send_json(data)
        time.sleep(1)
    print("Done")

    #####################
    # get the position of new node
    # get all elements from the next server position



def remove_node(servers, del_node):
    pass



def generate_data_consistent_hashing(servers):
    print("Starting...Consistent Hashing")
    ## TODO
    # hash servers to ring
    producers = create_clients(servers)
    bins_angle_to_name = dict()
    bin_angle_list = []
    for s in servers:
        bins_angle_to_name[hash_func(to_int(s))] = s 
        bin_angle_list.append(hash_func(to_int(s)))
    
    print(bin_angle_list)
    for num in range(10):
        data = { 'op':'PUT','key': f'key-{num}', 'value': f'value-{num}' }
        hashed_data = hash_func(to_int(data['key'])) 
        print("Key Hash value:", hashed_data)
        bin_angle_list.sort()
        angle = -1
        for i in bin_angle_list:
            if  i >= hashed_data:
                angle = i
                break
    
        if angle == -1:
            bin_to_be_hashed_to = bins_angle_to_name[bin_angle_list[0]]
            print("bin to be hashed to", bin_to_be_hashed_to)
        else:
            bin_to_be_hashed_to = bins_angle_to_name[angle]
            print("bin to be hashed to", bin_to_be_hashed_to)
        producers[bin_to_be_hashed_to].send_json(data)
        time.sleep(1)
    print("Done")

# ----------------------------------------------------------------------------------------------------------

def weight(server, key):
    a = 2347
    b = 1233
    return (a * (pow((a * server + b), (key), 3600)) + b)% 3600


def hrw_bin_to(servers, key):
    weights = dict()
    for server in servers:
        curr_weight = weight(to_int(server), to_int(key))
        weights[curr_weight] = server
        print("Weight calculated: ", curr_weight)
        print("Server Name ", server)
    max_weight = max(weights.keys())
    return weights[max_weight]
    
    
def generate_data_hrw_hashing(servers):
    print("Starting...HRW Hashing")
    ## TODO
    producers = create_clients(servers)
    for num in range(10):
        data = { 'op':'put','key': f'key-{num}', 'value': f'value-{num}' }
        print("Server List:", servers)
        print("Data to be hashed to", data['key'])
        bin_to_be_hashed_to = hrw_bin_to(servers, data['key'])
        print("Hashing to", bin_to_be_hashed_to)
        print("")
        producers[bin_to_be_hashed_to].send_json(data)
        time.sleep(1)
    print("Done")

# -----------------------------------------------------------------------------------------------------------------    
    
if __name__ == "__main__":
    # servers = []
    # num_server = 4
    c = consul.Consul()
    
    # Initial Service registration
    for i in range(4):
        port = 2000 + SERVER_PORT
        c.agent.service.register(name=f"127.0.0.1:200{SERVER_PORT}", port = port)
        SERVER_PORT += 1


    con_servers = list(c.agent.services().keys())
    servers = ["tcp://"+server for server in con_servers]


    # generate_data_round_robin(servers)
    generate_data_consistent_hashing(servers)
    # generate_data_hrw_hashing(servers)

    print("Adding New Node")
    add_node()

    # con_servers = list(c.agent.services().keys())
    # servers = ["tcp://"+server for server in con_servers]

    # generate_data_round_robin(servers)
   
