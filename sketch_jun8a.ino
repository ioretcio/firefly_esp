#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "TP-Link_97C7";
const char* password = "83003820";

const char* serverName = "HOST/imalive";

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
}

void loop() {
  if(WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverName);
    int httpResponseCode = http.GET();
    
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println(httpResponseCode);
      Serial.println(response);
    }
    else {
      Serial.print("Error on sending GET Request: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  }
  else {
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.println("Connecting to WiFi..");
    }
    Serial.println("Connected to the WiFi network");
  }
  delay(1000);
}