#TODO(done) : ALARM MSG !!BEAT au serv ;
#TODO(done) : soit !!cookie soit !!pseudo pour gerer les crashs
#TODO(done) : Recevoir cookie (avec select) 
#TODO(done) : Encapsulation des saisies client (!!message messageduclient)
#TODO(done) : Tolérance aux pannes des terminaux qui exécutent les commandes tail -f LOG et cat > TUBE, relance des terminaux et des commandes : 16/20
#TODO :Tolérances aux pannes de serveur (détection par échec d'envoi de message au serveur), commande !reconnect : 19/20


import os, socket, sys, select, time,signal


def alarm_hdler(sig_num,frame): 
	global server
	global server_statut
	msg="!!BEAT"
	try :
		server.send(msg.encode('utf-8')) #detection d'erreur
		signal.alarm(1)
	except :
		server_statut = False
	


	
def server_connection():
	HOST = sys.argv[1]
	PORT = int(sys.argv[2])
	sockaddr = (HOST, PORT)
	global server
	global server_statut
	try:
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPv4, TCP
		server.connect(sockaddr)
		if COOKIE :
			fd = os.open("/tmp/killer.cookie", os.O_RDONLY)
			fdr=os.read(fd,MAXBYTES).decode()
			print("Envoie du cookie au server... ")
			server.send(str('!!cookie '+fdr).encode())
			os.close(fd)
		else :

			server.send(str('!!pseudo ' + pseudo).encode())
			fd=os.open("/tmp/killer.cookie", os.O_WRONLY|os.O_CREAT)
			print("En attente de reception de cookie... ")
			cookie=server.recv(MAXBYTES).decode('utf-8')
			
			cookie = cookie.split()[1]
			print(cookie)
			os.write(fd,cookie.encode())
			os.close(fd)
		signal.signal(signal.SIGALRM, alarm_hdler)
		signal.alarm(1)
		print('connected to:', sockaddr)
		socketlist = [server]
		server_statut = True
		return True,socketlist,server
	except socket.error as e:
		print('erreur connexion:', e)
		sys.exit(1)



def help(fd):
    os.write(fd,"liste des commandes: \n".encode('utf-8'))
    os.write(fd,"	!quit pour quitter \n".encode('utf-8'))
    os.write(fd,"	!list pour lister les utilisateurs \n".encode('utf-8'))
    os.write(fd,"	!help pour afficher la liste des commandes \n".encode('utf-8'))
    os.write(fd,"	@pseudo message pour envoyer un message privé à :pseudo: \n".encode('utf-8'))
    os.write(fd,"	message pour envoyer un message public \n".encode('utf-8'))
    
def help_offline(fd):
	os.write(fd,"Vous n'êtes plus connecté au server \n\n".encode('utf-8'))
	os.write(fd,"Voici la liste des commandes hors-ligne: \n".encode('utf-8'))
	os.write(fd,"	!quit pour fermer le client \n".encode('utf-8'))
	os.write(fd,"	!help pour afficher la liste des commandes \n".encode('utf-8'))
	os.write(fd,"	!reconnect pour essayer de vous reconnecter au server\n".encode('utf-8'))

def term_saisie():    #tant que run == True, fermer un term le relance tout de suite
	global pathfifo
	while True :
		pid = os.fork()
		if pid == 0:
			argv=["xterm","-e","cat > "+pathfifo]
			os.execvp("xterm",argv) #lance le terminal ou entree standard > fifo
		else :
			os.wait()
			

def term_affichage():	#tant que run == True, fermer un term le relance tout de suite
	global pathlog
	while True :
		pid = os.fork()
		if pid == 0:
			argv1 =["xterm","-e","tail -f "+pathlog]
			os.execvp("xterm",argv1)
		else :
			os.wait()


def lancement_client(run,socketlist,server):
	os.mkfifo(pathfifo) #tube nommé pour communication entre terminal de saisie et superviseur
	
	pid = os.fork()
	quit = False
	if pid == 0:
		term_saisie()
	else :
		
		fifo=os.open(pathfifo,os.O_RDONLY) #descripteur de fichier fifo readonly
		socketlist.append(fifo)
		log=os.open(pathlog, os.O_APPEND|os.O_TRUNC|os.O_CREAT|os.O_WRONLY) #descripteur de fichier log append, create if not exist, supprime le contenu à l'ouverture
		pid2= os.fork()
		if pid2== 0:
			term_affichage()
		else:
			global server_statut
			help(log)
			while run :
				
				while server_statut :
					(activesockets, _, _) = select.select(socketlist, [], [])
					for s in activesockets:
						if s == fifo:
							
							line = os.read(fifo, MAXBYTES)
							lineD = line.decode()
							if lineD[0] == '!':
								if lineD == "!quit\n":
									server.close()
									run = False
									server_statut = False
									quit = True
									os.kill(pid,signal.SIGQUIT)
									os.kill(pid2,signal.SIGQUIT)
									break
								elif lineD == "!list\n":
									server.send(line)
								elif lineD == "!help\n":
									help(log)
								else:
									os.write(log,"commande inconnue\n".encode('utf-8'))
							else:
								line=("!!message "+line.decode()).encode()
								
								server.send(line)
						else:
							data = server.recv(MAXBYTES)
							if len(data) == 0:
								# run = False
								break
							if data.decode() != "!!BEAT\n":
								os.write(log, data)
								
				help_offline(log)
				offline = True
				
				while offline and not(quit):
					line = os.read(fifo, MAXBYTES)
					lineD = line.decode()
					if lineD[0] == '!':
						if lineD == "!quit\n":
							server.close()
							run = False
							server_statut = False
							quit = True
							os.kill(pid,signal.SIGQUIT)
							os.kill(pid2,signal.SIGQUIT)
							break
						elif lineD == "!help\n":
							help_offline(log)
						elif lineD == "!reconnect\n":
							offline = False
							run,socketlist,server=server_connection()
						else:
							os.write(log,"commande inconnue\n".encode('utf-8'))
			os.close(fifo)
			os.close(log)
			os.system("rm "+pathfifo)
			os.system("rm "+pathlog)
			os.system("pkill xterm") #ferme tous les processus xterm
			sys.exit(0)

def main():
	run,socketlist,servert=server_connection()
	lancement_client(run,socketlist,server)

	
if __name__ == "__main__":
	pidsupp=os.getpid()
	pathfifo = "/tmp/killer"+str(pidsupp)+".fifo"
	pathlog = "/tmp/killer"+str(pidsupp)+".log"
	MAXBYTES = 4096
	COOKIE = False
	server_statut = True
	if len(sys.argv) <= 2:
		print('Usage:', sys.argv[0], 'hote port')
		sys.exit(1)
	elif  not(os.path.exists("/tmp/killer.cookie")):
		pseudo = input("Entrez votre pseudo: ")
	else :
		COOKIE = True
	main()
