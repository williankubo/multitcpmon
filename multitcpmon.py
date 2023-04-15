import argparse, socket, errno, threading, queue, time, sys, os

output_stream = sys.stdout

#Initialize the parser
parser = argparse.ArgumentParser(description='A TCP Monitor connect status.')
parser.add_argument('File', help='file with host/ip,port,desc')
parser.add_argument('-tt', help='title')
parser.add_argument('-rf', help='refresh time (default 5s)')
parser.add_argument('-to', help='timeout time (default 1s)')
args = parser.parse_args()

#Retrieve parameter values from the parser arguments

#madatory values

ipfile=args.File
#print(ipfile)

#optional values

title = ""
if args.tt != None:
    title = args.tt
#print(title)

delay_refresh = 5
if args.rf != None:
    delay_refresh = float(args.rf)
#print(delay_refresh)

wait_return = 1
if args.to != None:
    wait_return = args.to
#print(wait_return)

"""
ports = range(1,1024)
if "-" in args.p:
    [minPort,maxPort] = [int(i) for i in args.p.split("-")]
    ports = range(minPort,maxPort+1)
elif args.p != None:
    ports = [int(i) for i in args.p.split(",")]
"""

# Define global variables

version = "v0.1"
lock = threading.Lock()
q = queue.Queue()


# open source_file
with open( ipfile, 'r') as source_file:
    # read lines from source_file
    lines = source_file.readlines()
    
    # remove empty lines
    no_empty_lines = [line.strip() for line in lines if line.strip()]
    
#print(no_empty_lines)

# init list
lines = []

# each line from source_file to line in list
for line in no_empty_lines:
    lines.append(line.strip().split(',')) # separate by ','

# do matriz from lines
new_data = [list(line) for line in lines]
#print(new_data)


# number of lines (hosts)
number_of_lines = len(new_data)


# add colum:  list[[ip,port,desc]] -> list[[ip,port,desc,status]
for i in range(number_of_lines):
    new_data[i].append("Wait")
#print(new_data)

# number of threads = number of lines 
threads = number_of_lines
#print(threads)


# class colors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[40;92m'
    OKWARNING = '\033[40;93m'
    WARNING = '\033[93m'
    FAIL = '\033[40;91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BG_RED = '\033[1;41m'
    BG_GREEN = '\033[1;42m'
    BG_BLK2 = '\033[40;1m'
    BG_BLK = '\033[40;0m'


# function to clear screen
clearConsole = lambda: os.system('cls' if os.name in ('nt', 'dos') else 'clear')


#connect(ip, port) - Connects to an ip address on a specified port to check if it is open
#Params:
#   ip - The ip to connect to
#   port - The port to connect to on the specified ip
#
#Returns: 'Open', 'Closed' or 'Timeout' depending on the result of connecting to the specified ip and port
def connect(ip, port):
    status = ""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        connection = s.connect((ip, port))
        status = "Open"
        s.close()

    except socket.timeout:
        status = "Timeout"


    except socket.error as e:
        if e.errno == errno.ECONNREFUSED:
            status = "Closed"
        else:
            raise e

    return status


#worker() - A function for worker threads to scan IPs and ports
def worker():
    while not q.empty():
        (ip,port,index) = q.get()
        status = connect(ip,port)
        lock.acquire()
        new_data[index][3] = status
        lock.release()
        q.task_done()


#init_pooling() - A function to prepare and start pooling to list host/ip:ports
def init_pooling():
    
    #Prepare queue
    for index in range(number_of_lines):
        q.put((new_data[index][0],int(new_data[index][1]),index))
        #print(new_data[index][0]+":"+new_data[index][1]+" index "+str(index))


    #Start threads
    for index in range(threads):
        t = threading.Thread(target=worker)
        t.start()

    q.join()



# init variable pooling
pooling = 0

# init variable time_start
time_start = time.time()

# clone new_data to current_data (reference to detect changes)
current_data = list(map(list, new_data))
#print(current_data)



# main loop
while True:

    # Print first screen

    if(pooling==0):
        clearConsole() #clear screen
        print(f'[ {bcolors.OKCYAN}{title}{bcolors.ENDC} - Multi TCP Monitor {version} ]')
        print()

        for index2 in range(len(new_data)):
            host = new_data[index2][0]
            ip = socket.gethostbyname(new_data[index2][0])
            port = new_data[index2][1]
            description = new_data[index2][2]
            status = new_data[index2][3]
            if (status == "Wait"):
                #print connection status
                print(f'{host}:{port} {ip} {bcolors.UNDERLINE}{description}{bcolors.ENDC} is {bcolors.OKWARNING}{status}{bcolors.ENDC}')
            elif (status == "Timeout"):
                #print connection status
                print(f'{host}:{port} {ip} {bcolors.UNDERLINE}{description}{bcolors.ENDC} is {bcolors.FAIL}{status}{bcolors.ENDC}')
            else:
                #print connection status
                print(f'{host}:{port} {ip} {bcolors.UNDERLINE}{description}{bcolors.ENDC} is {bcolors.OKGREEN}{status}{bcolors.ENDC}')
                

        print()
        
        #Update screen line Pooling
        output_stream.write('Pooling %s\r' % pooling)
        output_stream.flush()

        pooling = pooling + 1


    else:

        # save start time
        time_start = time.time()

        # Init Pooling
        init_pooling()

        if(new_data!=current_data):            # new_data updated, print new screen

            clearConsole() #clear screen
            print(f'[ {bcolors.OKCYAN}{title}{bcolors.ENDC} - Multi TCP Monitor {version} ]')
            print()

            for index2 in range(len(new_data)):
                host = new_data[index2][0]
                ip = socket.gethostbyname(new_data[index2][0])
                port = new_data[index2][1]
                description = new_data[index2][2]
                status = new_data[index2][3]
                if (status == "Wait"):
                    #print connection status
                    print(f'{host}:{port} {ip} {bcolors.UNDERLINE}{description}{bcolors.ENDC} is {bcolors.OKWARNING}{status}{bcolors.ENDC}')
                elif (status == "Timeout"):
                    #print connection status
                    print(f'{host}:{port} {ip} {bcolors.UNDERLINE}{description}{bcolors.ENDC} is {bcolors.FAIL}{status}{bcolors.ENDC}')
                else:
                    #print connection status
                    print(f'{host}:{port} {ip} {bcolors.UNDERLINE}{description}{bcolors.ENDC} is {bcolors.OKGREEN}{status}{bcolors.ENDC}')


            print()
            current_data = list(map(list, new_data)) #update current_data with nerw_data

        #Update screen line Pooling
        output_stream.write('Pooling %s\r' % pooling)
        output_stream.flush()

        pooling = pooling + 1

        # to avoid syn storm e high cpu (always wait refresh time)
        time_execution = time.time()-time_start
        if time_execution < delay_refresh:
            time_rest = delay_refresh - time_execution
            time.sleep(time_rest)
