import os, socket, sys, select
MAXBYTES = 4096
if len(sys.argv) == 3:
    pseudo = input("Entrez votre pseudo: ")
elif len(sys.argv) == 4:
    pseudo = sys.argv[3]
else:
    print('Usage:', sys.argv[0], 'hote port')
    sys.exit(1)
HOST = sys.argv[1]
PORT = int(sys.argv[2])
sockaddr = (HOST, PORT)

try:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPv4, TCP
    server.connect(sockaddr)
    server.send(str('!pseudo ' + pseudo).encode())
except socket.error as e:
    print('erreur connexion:', e)
    sys.exit(1)

print('connected to:', sockaddr)

def help():
    print("liste des commandes:")
    print("!quit pour quitter")
    print("!list pour lister les utilisateurs")
    print("!pseudo pour changer de pseudo")
    print("!help pour afficher la liste des commandes")
    print("@pseudo message pour envoyer un message privé à :pseudo:")
    print("message pour envoyer un message public")

help()
socketlist = [server, 0]
run = True
while run:
    (activesockets, _, _) = select.select(socketlist, [], [])
    for s in activesockets:
        if s == 0:
            line = os.read(0, MAXBYTES)
            if len(line) == 0:
                server.close()
                # s.shutdown(socket.SHUT_WR)
                run = False
                break
            lineD = line.decode()
            if lineD[0] == '!':
                if lineD == "!quit\n":
                    server.close()
                    run = False
                    break
                elif lineD == "!list\n":
                    server.send(line)
                elif lineD == "!help\n":
                    help()
                elif lineD[:7] == "!pseudo":
                    server.send(line)
                else:
                    print("commande inconnue")
            else:
                server.send(line)
        else:
            data = s.recv(MAXBYTES)
            if len(data) == 0:
                # run = False
                break
            os.write(1, data)
server.close()
sys.exit(0)
