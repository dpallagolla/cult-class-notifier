#!/usr/bin/env python

# [START imports]
import os
import urllib, json
import webapp2
from google.appengine.api import urlfetch
import re
from google.appengine.api import users
import logging


import sys
sys.path.insert(0, 'libs')

from bs4 import BeautifulSoup
import sendgrid

class workout:
    def __init__(self, sWorkoutName, sTime, sCenterName,sDate, sSeats):
        self.sWorkoutName = sWorkoutName
        self.sTime = sTime
        self.sCenterName = sCenterName
        self.sDate = sDate
        self.sSeats = sSeats

# [START main_page]
class MainPage(webapp2.RequestHandler):

    sQueryUrl = "https://www.cure.fit/cult/classbooking"
    
    def sendMail(self,sMailContent,sUsername,sEmail):
        sg = sendgrid.SendGridClient("<<your_send_grid_api_key>>")
        message = sendgrid.Mail()

        message.add_to(sEmail)
        message.set_from("<<sender_email>>")
        message.set_subject("Available cult classes")
        message.set_html(sMailContent)
        sg.send(message)
        return 

    def constructHTMLTable(self, aAllAvailableWorkouts):


        sHTMLTable = """ 
                    <!DOCTYPE HTML>
                    <html>
                        <head>
                        <meta http-equiv=3D "Content-Type" content=3D"text/html; charset=3Dutf-8" />
            <meta name=3D"viewport" content=3D"target-densitydpi=3Ddevice-dpi" /><meta =
            name=3D"viewport" content=3D"width=3Ddevice-width; initial-scale=3D1.0; max=
            imum-scale=3D1.0; user-scalable=3D0;" /><meta name=3D"apple-mobile-web-app-=
            capable" content=3D"yes" /><meta name=3D"HandheldFriendly" content=3D"true"=
            /><meta name=3D"MobileOptimized" content=3D"width" /> </head>
            <body>  
                    
        
        """

        sHTMLTable += """ <Table style="font-family: arial, sans-serif;border-collapse: collapse;width: 100%;"> 
        <tr> <th style="border: 1px solid #dddddd;text-align: left;padding: 8px;"> Workout Name </th> 
        <th style="border: 1px solid #dddddd;text-align: left;padding: 8px;"> Time </th> 
        <th style="border: 1px solid #dddddd;text-align: left;padding: 8px;"> Date </th> 
        <th style="border: 1px solid #dddddd;text-align: left;padding: 8px;"> Center </th> 
        <th style="border: 1px solid #dddddd;text-align: left;padding: 8px;"> seats </th> </tr> """

        for availableWorkoutCenter in aAllAvailableWorkouts:
            
            for oWorkout in availableWorkoutCenter:
                
                sHTMLTable += '<tr>'

                sHTMLTable += '<td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">'
                sHTMLTable += oWorkout.sWorkoutName
                sHTMLTable += '</td>' 

                sHTMLTable += '<td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">'
                sHTMLTable += oWorkout.sTime
                sHTMLTable += '</td>'   
                
                sHTMLTable += '<td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">'
                sHTMLTable += oWorkout.sDate
                sHTMLTable += '</td>'   
                
                sHTMLTable += '<td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">'
                sHTMLTable += oWorkout.sCenterName
                sHTMLTable += '</td>'   
                
                sHTMLTable += '<td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">'
                sHTMLTable += oWorkout.sSeats
                sHTMLTable += '</td>' 

                sHTMLTable += '</tr>'

        self.response.write(sHTMLTable)
        sHTMLTable += """</Table> </body> </html>"""
        return sHTMLTable

    def getAvailableWorkoutsForCenter(self,centerCode,aWorkouts):

        sCurrentQueryUrl = self.sQueryUrl + "/" + centerCode
        sCurrentQueryUrl += '?centerId=' + centerCode 
        pattern = 'window.__PRELOADED_STATE__ ='
        print sCurrentQueryUrl
        aAvailableWorkouts = []

        try:
            result = urlfetch.fetch(sCurrentQueryUrl)
            if result.status_code == 200:
                # self.response.write(result.content)
                soup = BeautifulSoup(result.content,'html.parser')
                scripts = soup.find_all('script')
                # self.response.write(scripts)
                for script in scripts:
                    # self.response.write(script)
                    script = str(script)
                    if(script.find(pattern) != -1):
                        script = script.replace(pattern,'')
                        script = script.replace('<script>','')
                        script = script.replace('</script>','')
                        script = script.replace('window.__SSR__ = true','')
                        jsonData = json.loads(script)
                        sCenterName = jsonData['cult']['booking']['title']
                        # self.response.write(sCenterName+'<br>')
                        aClassByDate = jsonData['cult']['booking']['classByDateList']

                        for dayClass in aClassByDate:
                            aClassesInDay = dayClass['classByTimeList']
                            for oClass in aClassesInDay:
                                if(len( oClass['classes']) > 0 ):
                                    print oClass['classes'][0]['state']
                                    if(oClass['classes'][0]['state'] == "AVAILABLE" and oClass['classes'][0]['workoutName'] in aWorkouts):
                                        # self.response.write(oClass['classes'][0]['workoutName']+'--')
                                        # self.response.write(oClass['classes'][0]['startTime']+'--')
                                        # self.response.write(oClass['classes'][0]['endTime']+'--')
                                        # self.response.write(str(oClass['classes'][0]['availableSeats'])+'--')
                                        # self.response.write(oClass['classes'][0]['date']+'<br>')
                                        oWorkout = workout(oClass['classes'][0]['workoutName'],oClass['classes'][0]['startTime'],sCenterName,oClass['classes'][0]['date'],str(oClass['classes'][0]['availableSeats']))
                                        aAvailableWorkouts.append(oWorkout)
                                        # print oWorkout
                if(len(aAvailableWorkouts)>0):
                    return aAvailableWorkouts
                else:
                    return None

                        
            else:
                self.response.status_code = result.status_code
        except urlfetch.Error:
            logging.exception('Caught exception fetching url')
        
    def get(self):

        # https://www.cure.fit/cult/classbooking/45?centerId=45

        #Center codes
        aRequestCenterCodes = self.request.get("centerCodes")
        #Workouts
        aRequestWorkouts = self.request.get("workouts")
        #interval
        interval = self.request.get("interval")
        #username
        sUsername = self.request.get("username")
        #email
        sEmail = self.request.get("email")
        

        aRequestCenterCodes = aRequestCenterCodes.split(',')
        aCenterCodes = []

        for sCenterCode in aRequestCenterCodes:
            aCenterCodes.append(sCenterCode)

        aRequestWorkouts = aRequestWorkouts.split(',')
        aWorkouts = []

        for sRequestWorkout in aRequestWorkouts:
            aWorkouts.append(sRequestWorkout)

        aAllAvailableWorkouts = []

        for centerCode in aCenterCodes:

            aAvailableWorkoutsForCenter = self.getAvailableWorkoutsForCenter(centerCode, aWorkouts)
            
            if(aAvailableWorkoutsForCenter != None):
                # print aAvailableWorkoutsForCenter
                aAllAvailableWorkouts.append(aAvailableWorkoutsForCenter)

        sMailContent = ""

        if len(aAllAvailableWorkouts) > 0:
            # self.response.write(aAvailableWorkouts)
            sMailContent = self.constructHTMLTable(aAllAvailableWorkouts)

        if sMailContent != "":
            self.sendMail(sMailContent,sUsername,sEmail)


        

        
# [END main_page]



# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)
# [END app]
