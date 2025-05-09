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

## LED and Push Button Connections

| Component | ESP32 Pin | Additional Notes |
|-----------|-----------|------------------|
| LED (Anode) | GPIO 15 | Use a 220Ω resistor in series |
| LED (Cathode) | GND | Ground connection |
| Push Button | GPIO 22 | Use a 10kΩ pull-down resistor |
| Push Button | 3.3V | Power connection |

## Code V1

```
/*
 * ESP32 IoT Project with Status Indicators & Train Status Management
 * 
 * LED Indications:
 * - LED starts glowing when initial setup completes (WiFi connected + valid GPS fix)
 * - LED stays on as long as WiFi is connected
 * - LED blinks briefly when HTTP request is successful
 * - LED turns off when WiFi connection fails
 * - LED turns on again if WiFi reconnects
 * - LED blinks continuously if train encounters any risk
 * 
 * Button Control:
 * - Press to toggle train operation mode:
 *   * When enabled: Sets train to "in_service_running" and begins sending location logs
 *   * When disabled: Sets train to "maintenance" and stops sending location logs
 */

#include <MFRC522v2.h>
#include <MFRC522DriverSPI.h>
#include <MFRC522DriverPinSimple.h>
#include <MFRC522Debug.h>
#include <TinyGPS++.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Define pins
const int LED_PIN = 15;      // GPIO pin for the LED
const int BUTTON_PIN = 22;   // GPIO pin for the push button

// WiFi credentials
const char* ssid = "Nav";       // Replace with your WiFi SSID
const char* password = "Navneet123#"; // Replace with your WiFi password

// API endpoints
const char* logsApiEndpoint = "https://iot-project-c3wb.onrender.com/api/logs/";
const char* statusApiEndpoint = "https://iot-project-c3wb.onrender.com/api/trains/%s/status";

// Train identification
const char* TRAIN_ID = "205";
const char* TRAIN_REF = "680296fc63fe290a1ff7e5c4";
const bool IS_TEST = true;

// Train status options
const char* STATUS_IN_SERVICE_RUNNING = "in_service_running";
const char* STATUS_MAINTENANCE = "maintenance";

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
  String utcTimestamp = "";
  
  // Validity flags
  bool rfidValid = false;
  bool gpsValid = false;
};

SensorData sensorData;

// Timing control
unsigned long lastDataInterval = 0;
const unsigned long DATA_INTERVAL = 6000;

unsigned long lastWifiCheckTime = 0;
const unsigned long WIFI_CHECK_INTERVAL = 5000;

// Button control variables
bool lastButtonState = HIGH;
bool currentButtonState = HIGH;
bool sendHttpRequests = true;  // Start with HTTP requests disabled (maintenance mode)
bool currentTrainStatus = false;  // false = maintenance, true = in_service_running
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;

// LED blink control
unsigned long ledBlinkStartTime = 0;
const unsigned long BLINK_DURATION = 1000;  // Total blinking duration (1 second)
unsigned long lastBlinkToggle = 0;
const unsigned long BLINK_INTERVAL = 200;   // Toggle every 200ms (5 blinks per second)
bool isBlinking = false;
bool blinkState = false;

// System status flags
bool wifiConnected = false;
bool gpsInitialized = false;
bool initialSetupComplete = false;
bool statusChangeRequested = false;

void setup() {
  Serial.begin(115200);
  while (!Serial);
  
  // Configure LED and button pins
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // Initialize LED state (off)
  digitalWrite(LED_PIN, LOW);
  
  // Initialize RFID
  mfrc522.PCD_Init();
  
  // Initialize GPS
  gpsSerial.begin(GPS_BAUD, SERIAL_8N1, RXD2, TXD2);
  
  // Connect to WiFi
  connectToWifi();
  
  Serial.println("System initialized, waiting for GPS fix...");
  
  // Set initial train status to maintenance
  if (wifiConnected) {
    setTrainStatus(STATUS_MAINTENANCE);
    currentTrainStatus = false;
  }
}

void loop() {
  // Check button state for operation mode toggle
  handleButtonPress();
  
  // Process RFID
  readRfidCard();
  
  // Process GPS
  readGpsData();
  
  // Update LED status based on current state
  updateLedStatus();
  
  // Check WiFi connection periodically
  if (millis() - lastWifiCheckTime >= WIFI_CHECK_INTERVAL) {
    checkWifiConnection();
    lastWifiCheckTime = millis();
  }
  
  // Handle data collection and API calls at regular intervals
  if (millis() - lastDataInterval >= DATA_INTERVAL) {
    printCombinedData();
    
    // Only send data if HTTP requests are enabled and initial setup is complete
    if (sendHttpRequests && initialSetupComplete && wifiConnected) {
      sendDataToAPI();
    }
    
    // Reset RFID data if no new card was detected in this cycle
    if (!sensorData.rfidValid) {
      sensorData.rfidUid = "null";
    }
    sensorData.rfidValid = false;
    
    lastDataInterval = millis();
  }
  
  // Handle train status change if requested
  if (statusChangeRequested && wifiConnected) {
    if (sendHttpRequests) {
      setTrainStatus(STATUS_IN_SERVICE_RUNNING);
      currentTrainStatus = true;
    } else {
      setTrainStatus(STATUS_MAINTENANCE);
      currentTrainStatus = false;
    }
    statusChangeRequested = false;
  }
}

void checkWifiConnection() {
  if (WiFi.status() != WL_CONNECTED) {
    wifiConnected = false;
    digitalWrite(LED_PIN, LOW);  // Turn off LED when WiFi disconnects
    connectToWifi();
  }
}

void updateLedStatus() {
  // If the LED is currently blinking due to successful HTTP request
  if (isBlinking) {
    // Check if the total blink duration has elapsed
    if (millis() - ledBlinkStartTime > BLINK_DURATION) {
      // Blinking finished, return to normal state
      isBlinking = false;
      digitalWrite(LED_PIN, wifiConnected ? HIGH : LOW);
    } else {
      // During blink period, toggle LED at regular intervals without delays
      if (millis() - lastBlinkToggle > BLINK_INTERVAL) {
        blinkState = !blinkState;  // Toggle the blink state
        digitalWrite(LED_PIN, blinkState ? HIGH : LOW);
        lastBlinkToggle = millis();
      }
    }
    return;
  }
  
  // Normal LED behavior: ON if initial setup is complete and WiFi is connected
  if (initialSetupComplete && wifiConnected) {
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }
}

void handleButtonPress() {
  // Read the current state of the button
  int reading = digitalRead(BUTTON_PIN);
  
  // If the button state changed, reset the debounce timer
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }
  
  // Only change the button state if the reading has been stable for debounceDelay
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != currentButtonState) {
      currentButtonState = reading;
      
      // If the button is pressed (LOW with pull-up resistor)
      if (currentButtonState == LOW) {
        // Toggle HTTP request state and request train status change
        sendHttpRequests = !sendHttpRequests;
        statusChangeRequested = true;
        
        // Log the new state for debugging
        Serial.print("Mode changed: ");
        if (sendHttpRequests) {
          Serial.println("Operational mode - HTTP requests enabled, setting train to in_service_running");
        } else {
          Serial.println("Maintenance mode - HTTP requests disabled, setting train to maintenance");
        }
      }
    }
  }
  
  lastButtonState = reading;
}

void connectToWifi() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  
  // Wait for connection with timeout
  unsigned long startAttemptTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 10000) {
    delay(500);
    Serial.print(".");
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected to WiFi with IP: " + WiFi.localIP().toString());
    wifiConnected = true;
    
    // Turn on LED if initial setup is already complete
    if (initialSetupComplete) {
      digitalWrite(LED_PIN, HIGH);
    }
    
    // Check if this completes the initial setup
    checkInitialSetupStatus();
  } else {
    Serial.println("\nFailed to connect to WiFi. Will retry later.");
    wifiConnected = false;
  }
}

void checkInitialSetupStatus() {
  // Initial setup is complete when both WiFi is connected and GPS has a valid fix
  if (!initialSetupComplete && wifiConnected && gpsInitialized) {
    initialSetupComplete = true;
    Serial.println("*** INITIAL SETUP COMPLETE ***");
    digitalWrite(LED_PIN, HIGH);  // Turn on LED when setup completes
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
      // Update satellite count and check if we have enough for valid GPS data
      sensorData.satellites = gps.satellites.isValid() ? gps.satellites.value() : 0;
      sensorData.gpsValid = (sensorData.satellites >= MIN_SATELLITES_FOR_VALID_DATA);
      
      // Update location data
      if (gps.location.isValid() && sensorData.gpsValid) {
        sensorData.latitude = gps.location.lat();
        sensorData.longitude = gps.location.lng();
        
        // Once we get valid GPS data, set GPS as initialized
        if (!gpsInitialized) {
          gpsInitialized = true;
          Serial.println("GPS initialized with valid fix!");
          
          // Update timestamp from GPS
          updateTimeFromGPS();
          
          // Check if this completes the initial setup
          checkInitialSetupStatus();
        }
      }
      
      // Update speed and altitude data if valid
      if (gps.speed.isValid() && sensorData.gpsValid) {
        sensorData.speed = gps.speed.kmph();
      }
      
      if (gps.altitude.isValid() && sensorData.gpsValid) {
        sensorData.altitude = gps.altitude.meters();
      }
      
      // Update HDOP data if valid
      if (gps.hdop.isValid()) {
        sensorData.hdop = gps.hdop.value() / 100.0;
      }
      
      // Always update time from GPS when available
      if (gps.time.isValid() && gps.date.isValid()) {
        updateTimeFromGPS();
      }
    }
  }
}

void updateTimeFromGPS() {
  if (gps.time.isValid() && gps.date.isValid()) {
    char dateTimeBuffer[30];
    
    // Format: YYYY-MM-DDTHH:MM:SSZ (ISO8601 format)
    sprintf(dateTimeBuffer, "%04d-%02d-%02dT%02d:%02d:%02dZ",
            gps.date.year(),
            gps.date.month(),
            gps.date.day(),
            gps.time.hour(),
            gps.time.minute(),
            gps.time.second());
    
    sensorData.utcTimestamp = String(dateTimeBuffer);
  }
}

void printCombinedData() {
  Serial.println("\n----- COMBINED DATA -----");
  
  // Print system status
  Serial.print("Initial setup complete: ");
  Serial.println(initialSetupComplete ? "Yes" : "No");
  
  Serial.print("WiFi Status: ");
  Serial.println(wifiConnected ? "Connected" : "Disconnected");
  
  Serial.print("Train Status: ");
  Serial.println(currentTrainStatus ? "in_service_running" : "maintenance");
  
  Serial.print("HTTP Requests: ");
  Serial.println(sendHttpRequests ? "Enabled" : "Disabled");
  
  // Print RFID data
  Serial.print("RFID Card UID: ");
  Serial.println(sensorData.rfidUid);
  
  // Print GPS data
  Serial.println("GPS Data:");
  Serial.print("  Satellites: "); 
  Serial.println(sensorData.satellites);
  
  Serial.print("  GPS Fix Quality: ");
  Serial.println(sensorData.gpsValid ? "Valid" : "Invalid");
  
  Serial.print("  Latitude: ");
  Serial.println(sensorData.gpsValid ? String(sensorData.latitude, 5) : "null");
  
  Serial.print("  Longitude: "); 
  Serial.println(sensorData.gpsValid ? String(sensorData.longitude, 5) : "null");
  
  Serial.print("  Speed: ");
  Serial.println(sensorData.gpsValid ? String(sensorData.speed) + " km/h" : "null");
  
  Serial.print("  Altitude: ");
  Serial.println(sensorData.gpsValid ? String(sensorData.altitude) + " meters" : "null");
  
  Serial.print("  HDOP: "); 
  Serial.println(gps.hdop.isValid() ? String(sensorData.hdop) : "null");
  
  Serial.print("  UTC Timestamp: ");
  Serial.println(sensorData.utcTimestamp);
  
  Serial.println("-------------------------------------------\n");
}

void setTrainStatus(const char* status) {
  // Only proceed if WiFi is connected
  if (!wifiConnected) {
    Serial.println("WiFi not connected. Cannot update train status.");
    return;
  }
  
  HTTPClient http;
  
  // Format the URL with the train ID
  char formattedUrl[200];
  sprintf(formattedUrl, statusApiEndpoint, TRAIN_REF);
  
  http.begin(formattedUrl);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("accept", "application/json");
  
  // Create JSON string with the status (needs to be a JSON string value)
  char jsonPayload[50];
  sprintf(jsonPayload, "\"%s\"", status);
  
  Serial.print("Updating train status to: ");
  Serial.println(status);
  Serial.print("URL: ");
  Serial.println(formattedUrl);
  Serial.print("Payload: ");
  Serial.println(jsonPayload);
  
  // Send PUT request
  int httpResponseCode = http.PUT(jsonPayload);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.print("Status update HTTP Response code: ");
    Serial.println(httpResponseCode);
    Serial.print("Response: ");
    Serial.println(response);
    
    // Blink LED to indicate successful status change
    if (httpResponseCode >= 200 && httpResponseCode < 300) {
      Serial.println("Train status updated successfully!");
      
      // Initialize blink sequence
      ledBlinkStartTime = millis();
      lastBlinkToggle = millis();
      blinkState = true;
      isBlinking = true;
      digitalWrite(LED_PIN, HIGH);
    }
  } else {
    Serial.print("Error updating train status. Error code: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

void sendDataToAPI() {
  // Only proceed if WiFi is connected
  if (!wifiConnected) {
    Serial.println("WiFi not connected. Cannot send data to API.");
    return;
  }
  
  HTTPClient http;
  http.begin(logsApiEndpoint);
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  StaticJsonDocument<512> jsonDoc;
  jsonDoc["train_id"] = TRAIN_ID;
  jsonDoc["train_ref"] = TRAIN_REF;
  
  // Use timestamp for API submission
  jsonDoc["timestamp"] = sensorData.utcTimestamp;
  
  // Handle RFID tag - properly set null in JSON when no tag detected
  if (sensorData.rfidUid != "null") {
    jsonDoc["rfid_tag"] = sensorData.rfidUid;
  } else {
    jsonDoc["rfid_tag"] = static_cast<const char*>(NULL);
  }
  
  // Add location as array only if GPS is valid
  if (sensorData.gpsValid) {
    JsonArray locationArray = jsonDoc.createNestedArray("location");
    locationArray.add(sensorData.longitude); // API format is [longitude, latitude]
    locationArray.add(sensorData.latitude);
    
    // Set accuracy based on HDOP
    String accuracy;
    if (sensorData.hdop < 1.0) {
      accuracy = "excellent";
    } else if (sensorData.hdop < 2.0) {
      accuracy = "good";
    } else if (sensorData.hdop < 5.0) {
      accuracy = "moderate";
    } else {
      accuracy = "poor";
    }
    jsonDoc["accuracy"] = accuracy;
  } else {
    // If GPS is not valid, set location to null
    jsonDoc["location"] = static_cast<const char*>(NULL);
    jsonDoc["accuracy"] = static_cast<const char*>(NULL);
  }
  
  jsonDoc["is_test"] = IS_TEST;
  
  // Serialize JSON to string
  String jsonPayload;
  serializeJson(jsonDoc, jsonPayload);
  
  // Send the request
  Serial.println("Sending data to API...");
  Serial.println(jsonPayload);
  
  int httpResponseCode = http.POST(jsonPayload);
  
  if (httpResponseCode > 0) {
    // Get the response
    String response = http.getString();
    
    // Print HTTP response code and full response payload
    Serial.println("HTTP Response code: " + String(httpResponseCode));
    Serial.println("Response: " + response);
    
    // Check if response code indicates success (2xx)
    if (httpResponseCode >= 200 && httpResponseCode < 300) {
      Serial.println("HTTP request successful! Blinking LED...");
      
      // Initialize blink sequence
      ledBlinkStartTime = millis();
      lastBlinkToggle = millis();
      blinkState = true;  // Start with LED ON
      isBlinking = true;
      
      // Turn on LED immediately for the first blink
      digitalWrite(LED_PIN, HIGH);
    }
  } else {
    Serial.print("Error code: ");
    Serial.println(httpResponseCode);
    Serial.println("API request failed");
  }
  
  http.end();
}
```