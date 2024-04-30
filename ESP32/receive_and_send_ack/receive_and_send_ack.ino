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
  String send = "ACK_" + message + '!';
  SerialBT.println(send);  // Acknowledgment message
  Serial.println("-> Sent: <" + send + ">");
  SerialBT.flush();
}

String readMessage(){
  String message = "";
  char ch;
  while(SerialBT.available()){
    ch = SerialBT.read();
    if(ch == '!')
      break;
    message += ch;
  }
  SerialBT.flush();
  return message;
}

void loop() {
  if (SerialBT.available()) {
    String message = readMessage();
    // String message = SerialBT.readString();
    // SerialBT.flush();
    Serial.println("<- Received: <" + message + ">");

    if(message == "stat_req"){
      int status = digitalRead(ledPin);

      if(status == 0){
        Serial.println("status 0");
        SerialBT.println("OFF!");
        SerialBT.flush();
      }
      else if(status == 1){
        Serial.println("status 1");
        SerialBT.println("ON!");
        SerialBT.flush();
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
  delay(100);
}
