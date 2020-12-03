import zmq
import sys
from  multiprocessing import Process
import consul
import time


SERVER_PROCESS_IDS = dict()
c = consul.Consul()

def server(port):
    context = zmq.Context()
    consumer = context.socket(zmq.PULL)
    consumer.connect(f"tcp://127.0.0.1:{port}")
    producer = context.socket(zmq.PUSH)
    producer.connect(f"tcp://127.0.0.1:3000")
    data = dict()
    
    while True:
        raw = consumer.recv_json()
        print(raw)
        if raw['op'] == 'GET_ALL':
            print(raw)
            json_list = []
            for key in data.keys():
                json_val = {'key' : key, 'value' : data[key]}
                json_list.append(json_val)
            json_string = {'Collection' : json_list}
            producer.send_json(json_string)
            print('sent')
            data = {}
        
        elif raw['op'] == 'PUT':
            key, value = raw['key'], raw['value']
            print(f"Server_port={port}:key={key},value={value}")
            data[key] = value
        
        elif raw['op'] == 'GET':
            json_string = {'key' : key, 'value' : data[key]}
            producer.send_json(json_string)
        
        else: 
            pass

def create_servers():
    con_servers = list(c.agent.services().keys())
    for s in con_servers:
        if s not in SERVER_PROCESS_IDS.keys():
            server_port = c.agent.services()[s]["Port"]
            print(f"Starting a server at:{server_port}...")
            process_id = Process(target=server, args=(str(server_port),))
            SERVER_PROCESS_IDS["127.0.0.1:"+str(server_port)] = process_id
            process_id.start()
            time.sleep(1)
    # print("create stop")

def delete_servers():
    con_servers = list(c.agent.services().keys())
    for sp in SERVER_PROCESS_IDS.keys():
        if sp not in con_servers:
            process_id = SERVER_PROCESS_IDS[sp]
            print(f"Removing server {sp}")
            process_id.terminate()
            SERVER_PROCESS_IDS.pop(sp)

        
if __name__ == "__main__":
    
    curr_num_servers = len(c.agent.services())
    create_servers()
    # print('end main')
    while True:

        con_num_servers = len(c.agent.services())
        if curr_num_servers < con_num_servers:
            # Create Server
            # servers_to_spawn = con_num_servers - curr_num_servers
            # print("creating servers")
            create_servers()
            curr_num_servers = con_num_servers

        elif curr_num_servers > con_num_servers:
            delete_servers()
            curr_num_servers = con_num_servers
            
        else:
            # time.sleep(1)
             pass
            # print("Waiting")
        time.sleep(1)

            # Delete Server
    # if len(sys.argv) > 1:
    #     num_server = int(sys.argv[1])
    #     print(f"num_server={num_server}")
        
    # for each_server in range(num_server):
    #     server_port = "200{}".format(each_server)
    #     print(f"Starting a server at:{server_port}...")
    #     Process(target=server, args=(server_port,)).start()

    # for each_server in range(num_server):
    #     server_port = "200{}".format(each_server)
    #     print(f"Starting a server at:{server_port}...")
    #     server_port = int(server_port)
    #     c.agent.service.register(name=f'127.0.0.1:{server_port}', address=f'127.0.0.1:{server_port}', port=server_port)
    #     Process(target=server, args=(server_port,)).start()


        

