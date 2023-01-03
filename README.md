Robot navigation
-

(This project was done as semestral work at CTU-FIT BI-PSI)


The goal of the task is to create a multi-threaded server for TCP/IP communication and implement the communication protocol
according to the given specification.

TASK:
Create a server to automatically control remote bots. The robots themselves log in to the server and it guides them to the center of the coordinate
system. For testing purposes, each robot starts at random coordinates and tries to reach the [0,0] coordinate. At the target coords, the robot
must pick up the secret. On the way to the destination, the robots may encounter obstacles that they must avoid.
The server can navigate multiple robots at the same time and implements a flawless communication protocol.

Full specification can be found in czech in specification.html.
