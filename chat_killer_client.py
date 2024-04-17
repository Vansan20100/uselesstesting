import os, socket, sys, select, time
pathfifo = "/tmp/killer.fifo"
pathlog = "/tmp/killer.log"



pid = os.fork()

if pid == 0:
	try :
		os.mkfifo(pathfifo)
	except :
		print("erreur fifo")
		try :
			sys.exit(0)
		except: 
			print("erreur d'exit")
	
	try :
		
		argv=["-e","cat > /tmp/killer.fifo"]
		os.execvp("xterm",argv)
	except :
		print("erreur xterm")

	
