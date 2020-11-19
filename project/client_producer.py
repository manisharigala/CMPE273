import zmq
import time
import sys
from itertools import cycle

def create_clients(servers):
    producers = {}
    context = zmq.Context()
    for server in servers:
        print(f"Creating a server connection to {server}...")
        producer_conn = context.socket(zmq.PUSH)
        producer_conn.bind(server)
        producers[server] = producer_conn
    return producers

def to_int(string):
    res = ""
    for char in string:
        res += str(ord(char))
    return int(res) 

def hash_func(x):
    a = 12345
    b = 123
    return (a*x + b) % 360 

def generate_data_round_robin(servers):
    print("Starting...Round Robin")
    producers = create_clients(servers)
    pool = cycle(producers.values())
    for num in range(10):
        data = { 'key': f'key-{num}', 'value': f'value-{num}' }
        print(f"Sending data:{data}")
        next(pool).send_json(data)
        time.sleep(1)
    print("Done")


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
        data = { 'key': f'key-{num}', 'value': f'value-{num}' }
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
        data = { 'key': f'key-{num}', 'value': f'value-{num}' }
        print("Server List:", servers)
        print("Data to be hashed to", data['key'])
        bin_to_be_hashed_to = hrw_bin_to(servers, data['key'])
        print("Hashing to", bin_to_be_hashed_to)
        print("")
        producers[bin_to_be_hashed_to].send_json(data)
        time.sleep(1)
    print("Done")
    
    
if __name__ == "__main__":
    servers = []
    num_server = 1
    if len(sys.argv) > 1:
        num_server = int(sys.argv[1])
        print(f"num_server={num_server}")
        
    for each_server in range(num_server):
        server_port = "200{}".format(each_server)
        servers.append(f'tcp://127.0.0.1:{server_port}')
        
    print("Servers:", servers)

    generate_data_round_robin(servers)
    generate_data_consistent_hashing(servers)
    generate_data_hrw_hashing(servers)
    
