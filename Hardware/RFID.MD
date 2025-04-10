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

## CODE

```

/*
  Rui Santos & Sara Santos - Random Nerd Tutorials
  Complete project details at https://RandomNerdTutorials.com/esp32-mfrc522-rfid-reader-arduino/
  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files.  
  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
*/

#include <MFRC522v2.h>
#include <MFRC522DriverSPI.h>
//#include <MFRC522DriverI2C.h>
#include <MFRC522DriverPinSimple.h>
#include <MFRC522Debug.h>

// Learn more about using SPI/I2C or check the pin assigment for your board: https://github.com/OSSLibraries/Arduino_MFRC522v2#pin-layout
MFRC522DriverPinSimple ss_pin(5);

MFRC522DriverSPI driver{ss_pin}; // Create SPI driver
//MFRC522DriverI2C driver{};     // Create I2C driver
MFRC522 mfrc522{driver};         // Create MFRC522 instance

void setup() {
  Serial.begin(115200);  // Initialize serial communication
  while (!Serial);       // Do nothing if no serial port is opened (added for Arduinos based on ATMEGA32U4).
  
  mfrc522.PCD_Init();    // Init MFRC522 board.
  MFRC522Debug::PCD_DumpVersionToSerial(mfrc522, Serial);	// Show details of PCD - MFRC522 Card Reader details.
	Serial.println(F("Scan PICC to see UID"));
}

void loop() {
	// Reset the loop if no new card present on the sensor/reader. This saves the entire process when idle.
	if (!mfrc522.PICC_IsNewCardPresent()) {
		return;
	}

	// Select one of the cards.
	if (!mfrc522.PICC_ReadCardSerial()) {
		return;
	}

  Serial.print("Card UID: ");
  MFRC522Debug::PrintUID(Serial, (mfrc522.uid));
  Serial.println();

  // Save the UID on a String variable
  String uidString = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) {
      uidString += "0"; 
    }
    uidString += String(mfrc522.uid.uidByte[i], HEX);
  }
  Serial.println(uidString);
}

```

## REFFERENCES
https://randomnerdtutorials.com/esp32-mfrc522-rfid-reader-arduino/