import network
import socket
import time
from machine import Pin, I2C
from BME280 import BME280

# Wi-Fi credentials
SSID = "Pi Pico W"
PASSWORD = "password"

i2c = I2C(0, scl=Pin(1), sda=Pin(0))  # Explicitly assign pins
bme = BME280(i2c=i2c)

# Start Wi-Fi Access Point (AP) mode
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD)

print("Setting up Wi-Fi network...")
while not ap.active():
    time.sleep(1)

print("Wi-Fi network ready!")
print("Network details:", ap.ifconfig())  # Print IP, subnet mask, gateway, DNS

# Create a socket to host the webpage
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print("Web server is running on:", ap.ifconfig()[0])

# Serve the webpage
def create_webpage(temperature, humidity, pressure):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BME280 Sensor Data</title>
        <meta http-equiv="refresh" content="5">
    </head>
    <body>
        <h1>BME280 Sensor Data</h1>
        <p><strong>Temperature:</strong> {temperature} </p>
        <p><strong>Humidity:</strong> {humidity} </p>
        <p><strong>Pressure:</strong> {pressure} </p>
    </body>
    </html>
    """

while True:
    cl, addr = s.accept()
    print('Client connected from', addr)
    
    try:
        # Read HTTP request
        request = cl.recv(1024)
        print("Request:", request)

        # Read BME280 sensor data
        temperature = bme.temperature
        pressure = bme.pressure
        humidity = bme.humidity

        # Generate the webpage with sensor data
        response = create_webpage(temperature, humidity, pressure)

        # Send HTTP response
        cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        cl.send(response)
    except Exception as e:
        print("Error:", e)
    finally:
        cl.close()
