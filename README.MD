DISCLAIMER: THIS IS FRONTEND UI IS PARTIALLY AI WRITTEN. I HAVE REVIEWED, MODIFIED, AND ADDED TO THE AI GENERATED CODE BUT PLEASE USE AT YOUR OWN RISK.

This is a simple Web UI for controlling the Taisen Netplay script on a DreamPi

To install:
* Place install.sh in a folder on your DreamPi
* Make it executable with the command `sudo chmod +x install.sh`
* Use the command `bash install.sh` to begin the installation. 

An alternate automated installer for Windows users can be found here:
https://github.com/likeagfeld/DreamPi-Link-Cable---Taisen-Netplay-Installer

The web UI can be reached at http://dreampi.local:1999

![Screenshot](https://github.com/eaudunord/taisen-web-ui/blob/main/Capture.PNG?raw=true)

# How to Play

*It's always a good idea to click "Check for updates" when you first load the page*

__*Do these steps before initiating a link cable game on the Dreamcast. You need to first establish a working tunnel between you and your opponent before a game can actually be played*__

1.  Select a COM port. On Raspberry Pi if you are using a USB-Serial adatper, it will likely appear as /dev/ttyUSB0

2.  Leave FTDI Latency at its default setting.

*Currently FTDI chipsets are not recommended for Virtual On. However if your adapter is FTDI, you can experiment with different latency settings here if you experience disconnects*

3.  Choose the game you are trying to play

4.  Choose a connection method
    * Matchmaking Server: This will attempt to connect you to another player who has requested to play the same game.
    * Direct IP Connection: This requires you to enter your opponent's IP address directly. In this mode one player chooses "Wait for Connection" and the other chooses "Connect to Opponent." If using a direct IP connection, both players will need to port forward ports 21001 and 21002 UDP to the Raspberry PI LAN address.

5. Start Link Cable

6. Check the black log window for script progress. 

*If you see the warning `Port in use. Try stopping Dreampi service or remove and reinsert USB adapter on Pi and try again` the Dreampi service is already listening on that port. You can either unplug and re-insert the adapter to unhook it from the Dreampi service, or stop the Dreampi service by clicking the "Dreampi Status" button and then the "Dreampi Service Running - Click to Stop" button.*

* Matchmaking flow
    * If no one is waiting for a match, you will see `match not found` and eventually it will stop at `Registered for a match` At this point you've informed the matchmaking server that you are waiting for a match for your chosen game. It will wait approximately 5 minutes for a match.
    * If a match is found, the status will update to `found opponent.`
    * Now the script will attempt to connect you to your opponent. If successful, the status will read `Connection established. Begin link play` at this point you can initiate a link mode game.


* Direct IP Connection flow
    * Both sides should start their link cable script. Even though one choice is 'Wait for Connection' the order in which each side starts the script doesn't matter.

    * Now the script will attempt to connect you to your opponent. If successful, the status will read `Connection established. Begin link play` at this point you can initiate a link mode game.

    __*For Virtual On there are some extra status messages to watch. You and your opponent should choose opposite sides, i.e. RNA and DNA. If one side chooses DNA, the status will update and tell you to choose RNA and vice versa. Virtual On has a much smaller initiation window than other games, so coordinate with your opponent when to start if possible. You and your opponent need to be using the same game region. Cross play between GDI and CDI does not work either. Only GDI to GDI and CDI to CDI.*__

    ![Screenshot](https://github.com/eaudunord/taisen-web-ui/blob/main/Capture2.PNG?raw=true)

