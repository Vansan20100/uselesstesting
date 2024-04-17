import os, sys, socket, select
HOST = "127.0.0.1"  # or 'localhost' or '' - Standard loopback interface address
PORT = 2009
MAXBYTES = 4096

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4, TCP
serversocket.bind((HOST, PORT))
serversocket.listen()
print("server listening on port:", PORT)
nb_open = 0

first = True
socketlist = [serversocket,0]
dicoClients = {}
dicoPseudo = {}






def mess_all(socketlist, s, msg):
    for c in socketlist:
        if c != serversocket and c != 0 and c != s:
                            # s.send(msg)
            c.send(msg)

while first or nb_open > 0:
    first = False
    (activesockets, _, _) = select.select(socketlist, [], [])
    for s in activesockets:
        if s == serversocket:
            (clientsocket, (addr, port)) = serversocket.accept()
            socketlist.append(clientsocket)
            # (pseudo, _) = clientsocket.recvfrom(MAXBYTES)
            pseudo = 'anonymous'
            dicoClients[clientsocket] = (addr, port, pseudo)
            dicoPseudo[clientsocket] = pseudo
            print(f"Incoming connection from {addr} on port {port}...")
            
            nb_open += 1

        elif s == 0:
            line = os.read(0, MAXBYTES).decode()
            if line[0] == '!':
                if line == "!quit\n":
                    print("Closing all connections and server...")
                    for c in socketlist:
                        if c != serversocket and c != 0:
                            c.close()
                            nb_open -= 1
                    serversocket.close()
                    break
            else:
                if line.split()[0] == 'wall':
                    msg = str("server: " + line.split(' ', 1)[1]).encode()
                    mess_all(socketlist, 0, msg)
                elif line.split()[0] == 'kick':
                    pseudo = line.split()[1]
                    if pseudo in dicoPseudo.values():
                        for c in socketlist:
                            if c != serversocket and c != 0:
                                if dicoClients[c][2] == pseudo:
                                    c.close()
                                    nb_open -= 1
                                    print(f"Kicking {pseudo}...")
                    else:
                        print(f"Le pseudo {pseudo} n'existe pas.")
        else:
            msg = s.recv(MAXBYTES)
            if len(msg) == 0:
                print(f"Connection from {dicoClients[s][0]} on port {dicoClients[s][1]} closed.")
                msg = str(f"[-]{dicoClients[s][2]}\n").encode()
                mess_all(socketlist, 0, msg)
                s.close()            
                socketlist.remove(s)
                nb_open -= 1
            else:
                text = msg.decode()
                if text[0] == '!': #commandes
                    if text == "!list\n":
                        s.send(str("Liste des clients connectés:\n").encode())
                        for c in socketlist:
                            if c != serversocket and c != 0:
                                s.send(str('-' + dicoClients[c][2] + "\n").encode())

                    elif text.split()[0] == "!pseudo":
                        if dicoPseudo[s] == "anonymous":
                            msg = str(f"[+]{text.split()[1]}\n").encode()
                            mess_all(socketlist, 0, msg)

                        dicoPseudo[s] = text.split()[1]
                        print(f"Connection from {dicoClients[s][2]} has changed pseudo to {dicoPseudo[s]}")
                        dicoClients[s] = (dicoClients[s][0], dicoClients[s][1], text.split()[1])

                elif text[0] == '@': #private message
                    pseudo = text.split()[0][1:]
                    msg = text.split(' ', 1)[1].encode()
                    if pseudo in dicoPseudo.values():
                        msg = str("Message privé de " + dicoClients[s][2] + ":" +  text.split(' ', 1)[1]).encode()
                        for c in socketlist:
                            if c != serversocket and c != 0:
                                if dicoClients[c][2] == pseudo:
                                    c.send(msg)
                    else:
                        msg = str("Le pseudo " + pseudo + " n'existe pas.\n").encode()
                        s.send(msg)
                
                else:              
                    msg = str(dicoClients[s][2] + ": " +  text).encode()
                    mess_all(socketlist, s, msg)

serversocket.close()
print("Last connection closed. Bye!")
sys.exit(0)