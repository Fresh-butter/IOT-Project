## GPS pin connections with ESP32

| ESP32 | GPS |
|-------|-----|
| VIN   | VCC |
| GND   | GND |
| D16   | TX |
| D17   | RX |

## MFRC522 RFID Reader Connections with ESP32

| MFRC522 RFID Reader | ESP32 | Description |
|---------------------|-------|-------------|
| SDA | GPIO 5 | SPI signal input, I2C data line, or UART data input |
| SCK | GPIO 18 | SPI clock |
| MOSI | GPIO 23 | SPI data input |
| MISO | GPIO 19 | SPI master-in-slave-out, I2C serial clock, or UART serial output |
| IRQ | Don't connect | Interrupt pin; signals the microcontroller when an RFID tag is nearby |
| GND | GND | Ground connection |
| RST | GPIO 21 | LOW signal to put the module in power-down mode; send a HIGH signal to reset the module |
| 3.3V | 3.3V | Power supply (2.5-3.3V) |


## Code V1

```
#include <MFRC522v2.h>
#include <MFRC522DriverSPI.h>
#include <MFRC522DriverPinSimple.h>
#include <MFRC522Debug.h>
#include <TinyGPS++.h>

// Pin definitions
#define RXD2 16
#define TXD2 17
#define GPS_BAUD 9600
#define RFID_SS_PIN 5

// Minimum satellites required for valid GPS data
#define MIN_SATELLITES_FOR_VALID_DATA 3

// RFID setup
MFRC522DriverPinSimple ss_pin(RFID_SS_PIN);
MFRC522DriverSPI driver{ss_pin};
MFRC522 mfrc522{driver};

// GPS setup
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);

// Data storage
struct SensorData {
  String rfidUid = "null";
  float latitude = 0;
  float longitude = 0;
  float speed = 0;
  float altitude = 0;
  int satellites = 0;
  float hdop = 0;
  String dateTime = "";
  
  // Validity flags
  bool rfidValid = false;
  bool gpsValid = false;
};

SensorData sensorData;

// Timing control
unsigned long lastPrintTime = 0;
unsigned long PRINT_INTERVAL = 6000; // Can be modified as needed

void setup() {
  Serial.begin(115200);
  while (!Serial);
  
  // Initialize RFID
  mfrc522.PCD_Init();
  
  // Initialize GPS
  gpsSerial.begin(GPS_BAUD, SERIAL_8N1, RXD2, TXD2);
  
  Serial.println("GPS and RFID Reader initialized");
}

void loop() {
  // Process RFID
  readRfidCard();
  
  // Process GPS
  readGpsData();
  
  // Print data at specified interval
  if (millis() - lastPrintTime >= PRINT_INTERVAL) {
    printCombinedData();
    
    // Reset RFID data if no new card was detected in this cycle
    if (!sensorData.rfidValid) {
      sensorData.rfidUid = "null";
    }
    sensorData.rfidValid = false;
    
    lastPrintTime = millis();
  }
}

void readRfidCard() {
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    sensorData.rfidUid = "";
    for (byte i = 0; i < mfrc522.uid.size; i++) {
      if (mfrc522.uid.uidByte[i] < 0x10) {
        sensorData.rfidUid += "0"; 
      }
      sensorData.rfidUid += String(mfrc522.uid.uidByte[i], HEX);
    }
    sensorData.rfidValid = true;
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
  }
}

void readGpsData() {
  while (gpsSerial.available() > 0) {
    if (gps.encode(gpsSerial.read())) {
      // Check if we have enough satellites for valid GPS data
      sensorData.satellites = gps.satellites.isValid() ? gps.satellites.value() : 0;
      sensorData.gpsValid = (sensorData.satellites >= MIN_SATELLITES_FOR_VALID_DATA);
      
      // Update location data
      if (gps.location.isValid() && sensorData.gpsValid) {
        sensorData.latitude = gps.location.lat();
        sensorData.longitude = gps.location.lng();
      }
      
      // Update speed data
      if (gps.speed.isValid() && sensorData.gpsValid) {
        sensorData.speed = gps.speed.kmph();
      }
      
      // Update altitude data
      if (gps.altitude.isValid() && sensorData.gpsValid) {
        sensorData.altitude = gps.altitude.meters();
      }
      
      // Update HDOP data
      if (gps.hdop.isValid()) {
        sensorData.hdop = gps.hdop.value() / 100.0;
      }
      
      // Update date/time data - time can be valid even without good GPS fix
      if (gps.date.isValid() && gps.time.isValid()) {
        // Convert UTC to IST (UTC+5:30)
int year = gps.date.year();
int month = gps.date.month();
int day = gps.date.day();
int hour = gps.time.hour();
int minute = gps.time.minute();
int second = gps.time.second();

// Add 5 hours and 30 minutes for IST
hour = hour + 5;
minute = minute + 30;

// Handle minute overflow
if (minute >= 60) {
  minute -= 60;
  hour++;
}

// Handle hour overflow (day change)
if (hour >= 24) {
  hour -= 24;
  day++;
  
  // Handle month end cases (simplified)
  int daysInMonth[] = {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
  
  // Adjust for leap year February
  if (month == 2 && year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)) {
    daysInMonth[2] = 29;
  }
  
  // Handle month rollover
  if (day > daysInMonth[month]) {
    day = 1;
    month++;
    
    // Handle year rollover
    if (month > 12) {
      month = 1;
      year++;
    }
  }
}

sensorData.dateTime = String(year) + "/" + 
                      (month < 10 ? "0" : "") + String(month) + "/" + 
                      (day < 10 ? "0" : "") + String(day) + "," + 
                      (hour < 10 ? "0" : "") + String(hour) + ":" + 
                      (minute < 10 ? "0" : "") + String(minute) + ":" + 
                      (second < 10 ? "0" : "") + String(second) + " IST";
      }
    }
  }
}

void printCombinedData() {
  Serial.println("\n----- COMBINED DATA -----");
  
  // Print RFID data
  Serial.print("RFID Card UID: ");
  Serial.println(sensorData.rfidUid);
  
  // Print GPS data
  Serial.println("GPS Data:");
  Serial.print("  Satellites: "); 
  Serial.println(sensorData.satellites);
  
  // Print GPS quality indicator
  Serial.print("  GPS Fix Quality: ");
  Serial.println(sensorData.gpsValid ? "Valid" : "Invalid");
  
  // Print location data
  Serial.print("  Latitude: ");
  Serial.println(sensorData.gpsValid ? String(sensorData.latitude, 5) : "null");
  
  Serial.print("  Longitude: "); 
  Serial.println(sensorData.gpsValid ? String(sensorData.longitude, 5) : "null");
  
  // Print speed data
  Serial.print("  Speed: ");
  if (sensorData.gpsValid) {
    Serial.print(sensorData.speed);
    Serial.println(" km/h");
  } else {
    Serial.println("null");
  }
  
  // Print altitude data
  Serial.print("  Altitude: ");
  if (sensorData.gpsValid) {
    Serial.print(sensorData.altitude);
    Serial.println(" meters");
  } else {
    Serial.println("null");
  }
  
  // Print HDOP data
  Serial.print("  HDOP: "); 
  Serial.println(gps.hdop.isValid() ? String(sensorData.hdop) : "null");
  
  // Print date/time data - can be valid even without good GPS fix
  Serial.print("  Date/Time: ");
  Serial.println(gps.date.isValid() && gps.time.isValid() ? sensorData.dateTime : "null");
  
  Serial.println("-------------------------------------------\n");
}


```

## Code V2