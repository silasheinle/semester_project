from BME280 import BME280  # Adjust if BME280.py is in a subdirectory
from machine import I2C, Pin
import time

def main():
    # Initialize I2C interface
    i2c = I2C(0, scl=Pin(1), sda=Pin(0))

    # Initialize the BME280 sensor
    try:
        bme = BME280(i2c=i2c)
    except Exception as e:
        print("Failed to initialize BME280:", e)
        return

    print("BME280 sensor initialized successfully.")
    print("Reading data...")

    # Continuously read and print temperature, pressure, and humidity
    try:
        while True:
            temperature = bme.temperature
            pressure = bme.pressure
            humidity = bme.humidity

            print(f"Temperature: {temperature}")
            print(f"Pressure: {pressure}")
            print(f"Humidity: {humidity}")
            print("-" * 30)

            time.sleep(2)  # Wait for 2 seconds before the next reading
    except KeyboardInterrupt:
        print("Test interrupted by user. Exiting...")

if __name__ == "__main__":
    main()
