# This is script that run when device boot up or wake from sleep.

import network, webrepl
sta_if = network.WLAN(network.STA_IF); sta_if.active(True)
sta_if.scan()                             # Scan for available access points
sta_if.connect("Kal-el", "superman") # Connect to an AP
sta_if.isconnected()                      # Check for successful connection
# Change name/password of ESP8266's AP:
# ap_if = network.WLAN(network.AP_IF)
# ap_if.config(essid="<AP_NAME>", authmode=network.AUTH_WPA_WPA2_PSK, password="<password>")
webrepl.start()