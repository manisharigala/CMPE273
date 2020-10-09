import schedule
import requests
import time
import yaml
import sys

#Parsing YAML 
if len(sys.argv) == 1:
    print("No input file")
    exit()
test_input = str(sys.argv[1])
with open(test_input) as file:
    input_list = yaml.load(file, Loader = yaml.FullLoader)


#Extracting Steps
steps_list = input_list['Steps']
steps = dict()
if len(steps_list) == 1:   
    steps[1] = steps_list[0]
else:
    steps[1] = steps_list[0]
    steps[2] = steps_list[1]


#Extracting Scheduler
scheduler = input_list['Scheduler']
[i] = scheduler['step_id_to_execute']
when = scheduler['when']

def invoke(step_id, data = ""):
    url = steps[step_id]['outbound_url']
    if url == "::input:data":
        url = data

    resp = requests.get(url)

    if resp.status_code == steps[step_id]['condition']['if']['equal']['right']:
        action = steps[step_id]['condition']['then']['action']
        if action == "::print":
            header = steps[step_id]['condition']['then']['data'].split(".")[-1]
            print(resp.headers[header])

        elif action == "::invoke:step:2":
            # call step2
            next_step_id = int(action.split("::invoke:step:")[1])
            data = steps[step_id]['condition']['then']['data']
            invoke(next_step_id, data)
    
    else:
        print(steps[i]['condition']['else']['data'])
    return


def job():
    invoke(i)
    return


def run_schedule(when):
    when = when.split(" ")
    first = when[0] == '*'
    second = when[1] == '*'
    third = when[2] == '*'
    days = {'0':'sunday', '1':'monday', '2':'tuesday', '3':'wednesday', 
            '4':'thursday', '5':'friday', '6':'saturday', '7':'sunday', '*':'day'}
    
    when0_okay = ((when[0].isnumeric() and int(when[0]) >= 0) and int(when[0]) <= 59) or first

    if (not when0_okay):
        print('Invalid Schedule')
        return
    
    if (not first) and (second) and (third):
        exec(f'schedule.every({when[0]}).minutes.do(job)')
    else:
        if first and second and third:
            print("Invalid schedule")
            return
        
        when1_okay = ((when[1].isnumeric() and int(when[1]) >= 0) and int(when[1]) <= 23) or second
        when2_okay  = ((when[2].isnumeric() and int(when[2]) >= 0) and int(when[2]) <= 7) or third

        if (not when0_okay) or (not when1_okay) or (not when2_okay):
            print("Invalid schedule")
            return

        m = ("0"*(2-len(when[0])) + when[0])*(when[0].isnumeric()) + "00"*(first)
        h = ("0"*(2-len(when[1])) + when[1])*(when[1].isnumeric()) + "00"*(second)
        cmd = f"schedule.every().{days[when[2]]}.at('{h}:{m}').do(job)"
        exec(cmd)

    return 


run_schedule(when)


while True:
    schedule.run_pending()
    time.sleep(1)

