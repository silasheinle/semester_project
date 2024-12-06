from utime import sleep
from machine import ADC, Pin

# Initialize ADC on pin GP26 (pin 31 on the Pico board)
adc_1 = ADC(Pin(26)) #speed
adc_2 = ADC(Pin(27)) #direction

print("Reading analog values from pin 31 (GP26):")
while True:
    raw_value_1 = adc_1.read_u16()  # Read raw ADC value (0-65535)
    voltage_1 = (raw_value_1 / 65535) * 3.3  # Convert to voltage (0-3.3V)
    raw_value_2 = adc_2.read_u16()  # Read raw ADC value (0-65535)
    voltage_2 = (raw_value_2 / 65535) * 3.3  # Convert to voltage (0-3.3V)
    print(f"Speed: {raw_value_1}, Voltage: {voltage_1:.2f} V")
    print(f"Direction {raw_value_2}, Voltage: {voltage_2:.2f} V")
    sleep(0.5)  # Delay for 1 second
