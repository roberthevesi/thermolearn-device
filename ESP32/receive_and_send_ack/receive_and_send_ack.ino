#include "BluetoothSerial.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth not enabled!
#endif

const int ledPin = 21;

BluetoothSerial SerialBT;

void setup() {
  delay(2000);
  Serial.begin(115200);
  SerialBT.begin("ESP32_BT");
  Serial.println("The device started, you can now pair it using Bluetooth.");

  pinMode(ledPin, OUTPUT);
}

void send_ack(String message){
  SerialBT.println("ACK_" + message);  // Acknowledgment message
  Serial.println("Sent ACK for " + message);
}

void loop() {
  if (SerialBT.available()) {
    String message = SerialBT.readString();
    Serial.println("Received: " + message);

    if(message == "stat_req"){
      int status = digitalRead(ledPin);

      if(status == 0){
        Serial.println("status 0");
        SerialBT.println("OFF");
      }
      else if(status == 1){
        Serial.println("status 1");
        SerialBT.println("ON");
      }
    }
    else if(message == "ON"){
      digitalWrite(ledPin, HIGH);
      send_ack(message);
    }
    else if(message == "OFF"){
      digitalWrite(ledPin, LOW);
      send_ack(message);
    }
    else{
      send_ack("unknown");
    }
  }
  delay(20);
}
