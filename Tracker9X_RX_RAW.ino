// Traker9X_RX_RAW -- based on Track9X_RX2
// Bob Senser, 05/16/2020
// used with RF9X
//
// BOARD: Pro Trinket V5/16 MHz (USB) 
// ISP: USBtinyISP
//
// Repurposed to work in "RAW" mode only
// 2021-11-06
// * add RAW MODE, lora to serial (no SD, etc)

// Based on "Sara Testbed"
//

#include <SPI.h>
#include <RH_RF95.h>

/************ Radio Setup ***************/
#define RF95_FREQ 915.0

#if defined (__AVR_ATmega328P__)  // Feather 328P w/wing
  #define RFM95_INT     3  // 
  #define RFM95_CS      10  //
  #define RFM95_RST     9  // "A"
  #define LED           13 // cannot use for blinking with SPI
#endif
#define BUFFER_SIZE 252
// #define SD_CS 4
#define BUZ_PIN 6

// buzzer 'thread' controller
long buzStop = 0;

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

void setup() 
{
  bool err = 0;
  Serial.begin(9600);
  // SPI init  
  pinMode(RFM95_CS, OUTPUT); 
  digitalWrite(RFM95_CS, HIGH);       
  pinMode(RFM95_RST, OUTPUT);
  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);
  // init buzzer & LED
  pinMode(BUZ_PIN, OUTPUT);
  digitalWrite(BUZ_PIN, HIGH);
  
  if (!rf95.init()) {
    Serial.println("#LoRa radio init failed");
    err = 1;
  }
  
  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("#setFrequency failed");
    err = 1;
  } else {
    Serial.print("#RFM95 radio @");  Serial.print((int)RF95_FREQ);  Serial.println(" MHz");
  }

  if (err == 1) {
    Serial.print("#Failed to Init!");     
    while (1) { }
  }
  // buzzzz
  buzOn(200);
}

void buzOn(int mSec) {
  buzStop = mSec + millis();
  digitalWrite(BUZ_PIN, LOW);
}
void buzOff() {
  if (millis() > buzStop) {
    digitalWrite(BUZ_PIN, HIGH);
    buzStop = 0;      
  }
  return;
}

void loop() {
  buzOff(); // poorman's thread....
  if (rf95.available()) {
    uint8_t buf[BUFFER_SIZE]; // [RH_RF95_MAX_MESSAGE_LEN + 8];
    uint8_t len = sizeof(buf);  
    if (rf95.recv(buf, &len)) {
      Serial.write((char *) buf, len);      
      buzOn(75);   // buzzzz          
    }
  } // of if available
} // of loop
