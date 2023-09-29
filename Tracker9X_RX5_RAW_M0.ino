// Traker9X_RX5_RAW_M0 -- based on Tracker9X_RX4_M0/Track9X_RX1
// Bob Senser, 2021-08-07
// used with RF9X
//
// created 2023-09-26
// to make a Q&D passthru for M0 that uses USB 
// port for IO.  Quiet and used LEDs
//
// for RFM95(X)
// RAW pass thru serial settings: rawMode = true
// 
//
char version[] = "RX5_RAW_M0";

// catchall buffer size -- set before includes
// old: #define BUFFER_SIZE 64
#define BUFFER_SIZE 252

#include <Wire.h> 
#include <RH_RF95.h>

/************ Radio Setup ***************/
#define RF95_FREQ 915.0

// changed for m0 LaRa
//                    new    old
#define RFM95_INT     3 // 3  // 
#define RFM95_CS      8 // 10  //
#define RFM95_RST     4 // 9  // "A"
#define LED           13

// manage multiple spi devices
// radio on above
#define SD_CS 15
#define BUZ_PIN 14

// status LEDs (two color)
// 3 LEDS, 2 pins per LED
const int statLEDs[] = {10, 9, 6, 5, 21, 20};
const int LEDoff = 0;
const int LEDred = 1;
const int LEDgreen = 2;

// ********** CONFIG *******************
const bool rawMode     = true;    
const bool buzzModeOn  = false;
const bool logPrefixOn = true;
const bool serialActive = true; 
const long heartbeatLimit = 500; // millisecs
// ********** CONFIG END *************

bool serialOutOn = true;
bool serial1OutOn = false;
// heartbeat timer

long clockBasis = 0;
long buzStop = 0;

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

int packetnum = 0;  // packet counter, we increment per xmission
const char OK[] = "OK";
const char FAILED[] = "FAILED";
const char RFMON[] = "RFM on";
const char RADIOERR[] = "Radio Err!";
const char RADIORST[] = "Radio Rst!";

void setLED(int _l, int _v) {
  int k = (_l * 2);
  switch (_v) {
    case (LEDoff): 
      digitalWrite(statLEDs[k], HIGH);
      digitalWrite(statLEDs[k+1], HIGH);
      break;      
    case (LEDred):
      digitalWrite(statLEDs[k], HIGH);
      digitalWrite(statLEDs[k+1], LOW);
      break;       
    case (LEDgreen):
      digitalWrite(statLEDs[k], LOW);
      digitalWrite(statLEDs[k+1], HIGH);
      break;       
  }
}

void setup() 
{
  
  char outConfig[64] = " = ";
  strcat(outConfig, version);
  strcat(outConfig, " ");  
  if (rawMode) { 
    strcat(outConfig,",RAW");
  }
  bool err = 0;
  if (serialActive > 0) {
    Serial.begin(9600); 
    while (!Serial) { delay(1); } // wait until serial console is open, remove if not tethered to computer
    Serial.print("Tacker9X_");
    Serial.print(version);
    Serial.print(" ");
    serialOutOn = true;       
  } 
  #if 0 
  if (serial1OutOn) {
    Serial1.begin(9600);
  }  
  #endif
   
  //manage multiple spi devices
  pinMode(SD_CS, OUTPUT);  // just in case SD is there 
  pinMode(RFM95_CS, OUTPUT); 
  digitalWrite(SD_CS, HIGH); // disable just in case
  digitalWrite(RFM95_CS, HIGH);       
  pinMode(RFM95_RST, OUTPUT);
  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);
  // init buzzer
  pinMode(BUZ_PIN, OUTPUT);
  digitalWrite(BUZ_PIN, HIGH);
  // simple LED
  pinMode(LED, OUTPUT);  
  digitalWrite(LED, HIGH);
  // init status LEDS
  for (int k=0; k < 6; k++) {
    pinMode(statLEDs[k], OUTPUT);  
    digitalWrite(statLEDs[k], HIGH);
  } 
    // start out red or off
  setLED(0,LEDred); 
  setLED(1,LEDoff); 
  setLED(2,LEDoff); 
  delay(1000); 
 
      
  if (!rf95.init()) {
    if (serialOutOn) {Serial.println("LoRa radio init failed");}
    err = 1;
  }

  if (!rf95.setFrequency(RF95_FREQ)) {
    if (serialOutOn) {Serial.println("setFrequency failed");}
    err = 1;
  } else {
    if (serialOutOn) {
      Serial.print("RFM95 radio @");
      Serial.print((int)RF95_FREQ);
      Serial.println(" MHz");
    }
  } 

  if (err == 1) {
    setLED(1,LEDred);    
    if (serialOutOn) {Serial.print("Failed to Init!");}     
    while (1) { }
  }
   
  Serial.print(RFMON);

  // watchdog timer
  clockBasis = millis();
  // Q&D config outout     
  char cstr[16];
  itoa(BUFFER_SIZE, cstr, 10);
  strcat(outConfig,",B");
  strcat(outConfig,cstr);

  uint8_t buf[BUFFER_SIZE]; 
  uint8_t buf2[BUFFER_SIZE];
  uint8_t buf3[BUFFER_SIZE];

  strcpy((char *) buf, outConfig);
  int len = strlen((char *) buf);
  buf3[0] = 0;   // no signal length   
  outLine(buf, buf2, buf3, len);
  // watchdog timer
  clockBasis = millis();   
  // all ready
  setLED(0,LEDgreen);
  setLED(1,LEDoff);  // just turn LED off    
}
void outLine(uint8_t buf[], uint8_t buf2[], uint8_t buf3[], int len) {
  uint8_t* outPtr;
  outPtr = buf;
  // rawMode: just write input to Serial
  // change for RAW_M0, send output to Serial not Serial1
  // Serial1.write((char *) outPtr, len);  // note use of write, not print
  Serial.write((char *) outPtr, len);  // note use of write, not print
  // no \n\r!
  return;
}

void buzOn(int mSec) {
  if (!buzzModeOn) return;
  buzStop = mSec + millis(); 
  digitalWrite(BUZ_PIN, LOW);
}
void buzOff() {
  if ((!buzzModeOn) || (millis() > buzStop) ) {
    digitalWrite(BUZ_PIN, HIGH); 
    buzStop = 0;     
  }
  return;
}

void loop() {
  if ((clockBasis + heartbeatLimit) < millis()) {
    digitalWrite(LED, !digitalRead(LED));
    clockBasis = millis(); 
  }  
  buzOff();
  if (rf95.available()) {
    setLED(1,LEDred);       
    // Should be a message for us now   
    uint8_t buf[BUFFER_SIZE]; // [RH_RF95_MAX_MESSAGE_LEN + 8];
    uint8_t buf2[BUFFER_SIZE * 2 + 16];  // made larger for nex convert on output
    uint8_t buf3[BUFFER_SIZE];       
    uint8_t len = sizeof(buf);   
    // get signal strength               
    sprintf((char *) buf3,"|%d", rf95.lastRssi()); 
    int len2 = 0; // strlen((char *) buf);
    if (logPrefixOn) {
      len2 = strlen((char *) buf3);
    }    
    if (rf95.recv(buf, &len)) {        
      buf[len] = 0;
      // output in buf, length in len
      outLine(buf, buf2, buf3, len);         
      // buzzzz
      buzOn(75);           
      len = strlen((char *) buf); // now len of all used space         
    } else {
      if (serialOutOn) {
        Serial.print("Rec ");
        Serial.println(FAILED);
      } 
    }
    delay(25);  // so can be seen
    setLED(1,LEDoff);
  
 } // of if available
} // of loop
