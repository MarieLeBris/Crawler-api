#import 
import os
import json
import flask
import config #made by girls
from flask import Flask
from time import sleep
from datetime import timedelta
from flask import request, jsonify
from flask import session
import datetime
from flask_cors import CORS
from crawler import CRAWLER #made by girls
from compass import COMPASS #made by girls
from motor import MOTOR #made by girls


#API creation
app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config["DEBUG"] = True

cors = CORS(app)

#call classes
## crawler type object
CR = CRAWLER()
## compass type object
CP = COMPASS(config.I2C_adresse)

## motor type objet (motor right)
MR = MOTOR(config.motor_right_IO2,config.motor_right_DIR,0)
## motor type objet (motor left)
ML =MOTOR(config.motor_left_IO2,config.motor_left_DIR,1)

#initialization of global variables
compteur_test=0
test_recaption = False
orderreceiv = "error"
accessWebPage  = False
total_turn = 0




## Returns the current date
#  @return: the date in YYYY / MM / DD HH / MM / SS format
#  @type; string
def date():
	now = datetime.datetime.now()
	return (now.strftime("%Y/%m/%d /%H/%M/%S"))



## Management of displacement in manual mode
#  Processing of requests sent for manual mode.
#  If the request is correct:
#  -retrieves data from the requests.
#  -processes the data received.
#  -create the character chain with the information received and process.
#  -confirm that the request has been received correctly
#  -execute the order given during the time requested.
#  -stop execution and order to stop the crawler if another request is sent for a new move or for the order to stop.
#  -confirms the end of the order
#  Otherwise indicates that the received request is incorrect
#  @return: if correct request return ,at the end of the order, "date+"Crawler send :/order:"+order number+" END""", if error at reception returns "date+"Crawler send :/order:"+sorder number+" error in request""
#  @type: string
def manual_deplacement():
    #global variable
    global compteur_test
    global test_recaption
    global orderreceiv
    global total_turn
    compteur_test+=1
    if 'time' in request.args and 'speed' in request.args and 'direction' in request.args and 'order' in request.args and 'nborder' in request.args:
        #argument retrieval
        ordersend = request.args['order']
        nborder = request.args['nborder']
        time = request.args['time']
        speed = request.args['speed']
        direction = request.args['direction']
	##### Condition exist text #####
	#labview_file=open("trama_test.txt","w+")
        #writes in the test file that the request was sent
		# MODIFICAT str() 06-11-2020 14.34
        trun_degree =CP.bearing3599()
        compteur = 0
        if str(direction) == "forward":
            CR.forward(int(speed))
        elif str(direction) == "backward":
            CR.backward(int(speed))
        elif str(direction) == "right":
            CR.right(int(speed))
        elif str(direction) == "left":
            CR.left(int(speed))
        else :
            return "Error direction"

        #write in the file that the request has been received
        orderreceiv = str(date())+"Crawler send :/order:"+str(nborder)+"/Time:"+str(time)+"/speed:"+str(speed)+"/direction:"+direction
        test_recaption = True

        value=compteur_test
        while compteur_test==value and compteur < int(time):
            sleep(1)
            compteur+=1
        if compteur == int(time):
            CR.forward(0)
        test_recaption = False

        #write in the file that the order has been executed
        orderend = str(date())+"Crawler send :/order:"+str(nborder)+" END"
        if direction == "right" :
            total_turn = total_turn  + (trun_degree + CP.bearing3599())
        elif total_turn == "left":
            total_turn = total_turn - (trun_degree + CP.bearing3599())

        return orderend
    else:
        error_arguments = str(date())+"Crawler send :/order:"+str(nborder)+" error in request"
        return error_arguments
    
    





## Management of displacement in automatic mode
#  Processing of requests sent for automatic mode.
#  If the request is correct:
#  -retrieves data from the requests.
#  -processes the data received.
#  -create the character chain with the information received and process.
#  -confirm that the request has been received correctly
#  -execute the order given during the time requested.
#  -stop execution and order to stop the crawler if another request is sent for a new move or for the order to stop.
#  -confirms the end of the order
#  Otherwise indicates that the received request is incorrect
#  @return: if correct request return ,at the end of the order, "date+"Crawler send :/order:"+ first order number + last order number+" END""", if error at reception returns "date+"Crawler send :/order:"+sorder number+" error in request""
#  @type: string
def automatic_deplacement():
    #global variable
    global compteur_test
    global orderreceiv
    compteur_test+=1
    global test_recaption
    global total_turn
    
    if 'order' in request.args and 'nborder' in request.args and 'nborderend' in request.args and 'number' in request.args:
        #argument retrieval
        ordersend = request.args['order']
        nborder = request.args['nborder']
        nborder2 = request.args['nborderend']
        nb_element = int(request.args['number'])

        
        #write in the file that the request has been received
        orderreceiv = str(date())+"Crawler send :/order:"+str(nborder)+" " +str(nborder2)

        #argument retrieval
        for i in range (1, nb_element+1):
            #argument retrieval
            time = request.args['time'+str(i)]
            speed1= request.args['speed1'+str(i)]
            speed2 = request.args['speed2'+str(i)]
            orderreceiv += "/time"+str(i)+":"+str(time)+"/Motor right"+str(i)+":"+str(speed1)+"/Motor left"+str(i)+":"+str(speed2)
        test_recaption = True
        for i in range(1,nb_element+1):
            #argument retrieval
            time = request.args['time'+str(i)]
            speed1= request.args['speed1'+str(i)]
            speed2 = request.args['speed2'+str(i)]
            
            if int(speed1) < 0:
                MR.DIR(config.motor_right_DIR,0)
                MR.duty_cycle(int(speed1), config.motor_right_PWM )
            else :
                MR.DIR(config.motor_right_DIR,1)
                MR.duty_cycle(int(speed1),config.motor_right_PWM)
            if int(speed2) < 0:
                ML.DIR(config.motor_left_DIR,0)
                ML.duty_cycle(int(speed2),config.motor_left_PWM)
            else :
                ML.DIR(config.motor_left_DIR,1)
                ML.duty_cycle(int(speed2),config.motor_left_PWM)  
            value=compteur_test
            trun_degree =CP.bearing3599()
            compteur =0
            while compteur_test==value and compteur < int(time):
                sleep(1)
                compteur+=1
            if compteur == int(time):
                CR.forward(0)
            test_recaption = False
            #write in the file that the order has been executed
            orderend = str(date())+"/order:"+str(nborder)+" "+str(nborder2)+" END"
            if speed2 >= speed1 :
                total_turn = total_turn  + (trun_degree + CP.bearing3599())
            elif speed1 >= speed2:
                total_turn = total_turn - (trun_degree + CP.bearing3599())
        return orderend
    else :
        error_js = str(date()) +"/order:"+str(nborder)+" "+str(nborder2)+" error in request"
        return error_js






## Management of displacement in advanced mode
#  Processing of requests sent for advanced mode.
#  If the request is correct:
#  -retrieves data from the requests.
#  -processes the data received.
#  -create the character chain with the information received and process.
#  -confirm that the request has been received correctly
#  -execute the order given during the time requested.
#  -stop execution and order to stop the crawler if another request is sent for a new move or for the order to stop.
#  -confirms the end of the order
#  Otherwise indicates that the received request is incorrect
#  @return: if correct request return ,at the end of the order, "date+"Crawler send :/order:"+order number+" END""", if error at reception returns "date+"Crawler send :/order:"+sorder number+" error in request""
#  @type: string
def advanced_deplacement():
    #global variable
    global compteur_test
    global test_recaption
    global orderreceiv
    global total_turn
    compteur_test+=1
    if 'time' in request.args and 'speed1' in request.args and 'speed2' in request.args and 'order' in request.args and 'nborder' in request.args:

        #argument retrieval
        ordersend = request.args['order']
        nborder = request.args['nborder']
        time = request.args['time']
        speed1 = request.args['speed1']
        speed2 = request.args['speed2']


        #traiteement de la direction
        if int(speed1) < 0:
            MR.DIR(config.motor_right_DIR,0)
            MR.duty_cycle(int(speed1), config.motor_right_PWM )
        else :
            MR.DIR(config.motor_right_DIR,1)
            MR.duty_cycle(int(speed1),config.motor_right_PWM)
        if int(speed2) < 0:
            ML.DIR(config.motor_left_DIR,0)
            ML.duty_cycle(int(speed2),config.motor_left_PWM)
        else :
            ML.DIR(config.motor_left_DIR,1)
            ML.duty_cycle(int(speed2),config.motor_left_PWM) 

        #write in the file that the request has been received
        orderreceiv = str(date())+"Crawler send :/order:"+str(nborder)+"/Time:"+str(time)+"/Motor right:"+str(speed1)+"/Motor left:"+str(speed2)
        test_recaption = True

        #iniatialisation des valeur pour while
        value=compteur_test
        trun_degree =CP.bearing3599()
        compteur =0
        while compteur_test==value and compteur < int(time):
            sleep(1)
            compteur+=1
        #si le while va jusqua la fin
        if compteur == int(time):
            CR.forward(0)

        #arret du robot quand action fini
        CR.forward(0)
        test_recaption = False

        #write in the file that the order has been executed
        orderend = str(date())+"/order:"+str(nborder)+" END"
    else:
        return "Error: arguments non spécifiés"
        test_recaption = False
    if speed2 >= speed1 :
        total_turn = total_turn  + (trun_degree + CP.bearing3599())
    elif speed1 >= speed2:
        total_turn = total_turn - (trun_degree + CP.bearing3599()) 
    return orderend







## Management of rotation
#  Processing of requests sent for rotation mode.
#  If the request is correct:
#  -retrieves data from the requests.
#  -processes the data received.
#  -create the character chain with the information received and process.
#  -confirm that the request has been received correctly
#  -rotate the robot until it faces the chosen direction
#  -stop execution and order to stop the crawler if another request is sent for a new move or for the order to stop.
#  -send response to the request that the order is finished
#  Otherwise indicates that the received request is incorrect
def turn():
    #global variable
    global compteur_test
    global test_recaption
    global orderreceiv
    global total_turn
    test_recaption = True
    compteur_test+=1
    if 'compassvalue' in request.args and 'order' in request.args and 'nborder' in request.args:
        #argument retrieval
        ordersend = request.args['order']
        nborder = request.args['nborder']
        direction = request.args['compassvalue']

        #write in the file that the request has been received
        orderreceiv = str(date())+" Crawler send/order:"+str(nborder)+"/rotation:"+direction
        test_recaption = True
        #boucle d'execution de la fonction demander
        if total_turn >= 360 :
            total_turn = total_turn + CP.bearing3599()
            CR.left(50)
        elif total_turn <= -360 :
            total_turn = total_turn - CP.bearing3599()
            CR.right(50)
        elif direction <= 180 :
            total_turn = total_turn - CP.bearing3599()
            CR.right(50)
        else :
            total_turn = total_turn + CP.bearing3599()
            CR.left(50)
        while (int(direction) <= int(CP.bearing3599()) +config.compass_accuracy) and (int(direction) >= int(CP.bearing3599()) - config.compass_accuracy):
            sleep(0.5)
        #arret du robot quand l'action à été faite
        CR.right(0)
        #write in the file that the order has been executed
        orderend = str(date())+" Crawler send /order:"+str(nborder)+" END"
        return orderend
    else:
        return "Error: arguments non spécifiés"

## Test if a second request is received: 
#  wait for confirmation that the second request is received,
#  when the second is received and processed, returns in response to the first request that the second has been correctly received
#  @return: orderreceiv
#  @type: string
def testReception():
    global orderreceiv
    while test_recaption == False:
        sleep(0.001)
    return orderreceiv

## Stop any function during execution
#  @return: "Application stop"
#  @type: string
def stopfunction() :
    global compteur_test
    global test_recaption
    global orderreceiv
    orderreceiv = "STOP"
    test_recaption = True
    CR.forward(0)
    compteur_test=0
    test_recaption = False
    return "Aplication Stop"

## test if a person is already connected to the web page
#  @return: 0 if access to the web page is possible, 1 otherwise
#  @type: string
def connec():
    #CR.init_IO2_DIR()
    #CR.init_PWM()
    global accessWebPage
    if accessWebPage == False:
        accessWebPage = True
        return str(0)
    else :
        return str(1)
	
## free access to the web page
#  @return: 1
#  @type: string
def deco():
    global accessWebPage
    accessWebPage = False
    return str(1)



@app.route("/api/test")
## if request send to "/api/test", execute testRecpetion() and send in response to the request the value return by testReception ()
#  @return: value return by testRecption()
#  @type: string
def reception():
    return testReception()


@app.route("/api/stop")
## if request send to /api/stop, execute stopfunction() and send in response to the request the value return by stopfunction()
#  @return: value return by stopfunction()
#  @type: string
def set_stop_run():
    return stopfunction()

@app.route("/api/read_compass")
## if request send to /api/read_compass, execute bearing3599() from COMPASS class and send in response to the request the value return by bearing3599()
#  @return: value return by bearing3599()
#  @type: string
def read_compass():
    compass = CP.bearing3599()
    return str(compass)


@app.route("/api/manual/deplacement")
## if request send to /api/manual/deplacment, execute manual_deplacment() and send in response to the request the value return by manual_deplacment()
#  @return: value return by manual_deplacment()
#  @type: string
def run_manual():
    return manual_deplacement()

    

@app.route("/api/automatic/deplacement")
## if request send to /api/automatic/deplacement, execute automatic_deplacement() and send in response to the request the value return by automatic_deplacement()
#  @return: value return by automatic_deplacement()
#  @type: string
def run_automatic():
    return automatic_deplacement()


@app.route("/api/advanced/deplacement")
## if request send to /api/advaned/deplacement, execute advanced_deplacement() and send in response to the request the value return by advanced_deplacement()
#  @return: value return by advanced_deplacement()
#  @type: string
def run_advanced():
    return advanced_deplacement()


@app.route("/api/rotation")
## if request send to /api/rotation, execute turn() and send in response to the request the value return by turn()
#  @return: value return by turn()
#  @type: string
def rotation():
    return turn()

@app.route("/api/connectiontest")
## if request send to /api/connectiontest, return ok
#  @return: "ok"
#  @type: string
def connectionTest():
    return "ok"


@app.route("/api/hour")
## if request send to /api/hour, execute date() and send in response to the request the value return by date()
#  @return: value return by date()
#  @type: string
def hourCrawler():
    return date()

@app.route("/api/connection")
## if request send to /api/connection, execute connection() and send in response to the request the value return by connection()
#  @return: value return by connection()
#  @type: string
def connnection():
    return connec()

@app.route("/api/deconnection")
## if request send to /api/deconnection, execute deconnection() and send in response to the request the value return by deconnection()
#  @return: value return by deconnection()
#  @type: string
def deconnection():
    return deco()


if __name__=="__main__":
	#MODIFICAT 23/10/2020 12:19
    app.run(host='147.83.159.170', port=5001, debug=True)
	#app.run(host='147.83.159.154', port=5001, debug=True)
    #app.run(host='192.168.2.117', port=5001, debug=True)
    #app.run(host='127.0.0.1', port=5001, debug=True)
