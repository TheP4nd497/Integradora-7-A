
#include <Servo.h>
#include <DHT.h>		// importa la Librerias DHT
#include <DHT_U.h>

#define MQ2_PIN A3   // sensor de gas 
#define sonido_mic 10     // sensor de sonido
#define sens_mic A4
#define LDRPIN 5      //sensor de luz
#define agua_pin A5       // SENSOR DE AGUA 
int dhtsens = 7;			// pin DATA de DHT22 a pin digital 2
int servo1_pin = 4;
int servo2_pin = 8;
int TEMPERATURA;
int HUMEDAD;
int gas;
int agua;
int valor_son;
int sens ;
Servo servo1;
Servo servo2;
// Variables to track time
unsigned long previousMillis = 0;
const long interval = 10000; // 10 seconds in milliseconds

// Variable to track servo state (true = 90deg, false = 0deg)
bool isAtNinety = false;


DHT dht(dhtsens, DHT11);		// creacion del objeto, cambiar segundo parametro
				// por DHT11 si se utiliza en lugar del DHT22
void setup(){
  Serial.begin(9600);		// inicializacion de monitor serial
  dht.begin();			// inicializacion de sensor

  servo1.attach(servo1_pin);
  servo2.attach(servo2_pin);
  
  // Start at 0
  servo1.write(0);
  servo2.write(90);
}

void loop(){
  unsigned long currentMillis = millis();
  // Check if 10 seconds have passed
  if (currentMillis - previousMillis >= interval) {
    // Save the last time we moved
    previousMillis = currentMillis;

    if (isAtNinety) {
      // If currently at 90, go to 0
      servo1.write(90);
      servo2.write(0);
      isAtNinety = false;
    } else {
      // If currently at 0, go to 90
      servo1.write(0);
      servo2.write(90);
      isAtNinety = true;
    }
  }

  //AGUA
  agua = analogRead(agua_pin);

  //mq2
  gas = analogRead(MQ2_PIN);	


  //dht 11
  TEMPERATURA = dht.readTemperature();	// obtencion de valor de temperatura
  HUMEDAD = dht.readHumidity();		// obtencion de valor de humedad

  //sonido
  valor_son = digitalRead(sonido_mic);
  sens = analogRead(sens_mic);
  

  //luz
 /** int32_t luz = digitalRead(LDRPIN);
    Serial.print(" ");
  if(luz == 1 ){
    Serial.println("Foco Apagado ");
  }else{
    Serial.println("Foco Encendido ");
  }
  **/

   Serial.print("GAS01:");
  Serial.print(gas);
  Serial.print("HUM01:");
  Serial.print(HUMEDAD);
  Serial.print("TEMP01:");
  Serial.print(TEMPERATURA);
   Serial.print("AGU01:");
  Serial.print(agua);
  Serial.print("SON01:");
  if (valor_son == HIGH){
   Serial.println(1); 
  }else{
    Serial.println(0);
  }

  delay(1000);
}
