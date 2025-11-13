#include <DHT.h>		// importa la Librerias DHT
#include <DHT_U.h>

#define MQ2_PIN A0    // sensor de gas 
#define sonido A1     // sensor de sonido
#define LDRPIN 5      //sensor de luz
int dhtsens = 7;			// pin DATA de DHT22 a pin digital 2
int TEMPERATURA;
int HUMEDAD;
int gas;
//int valor_son;
int umbralSonido = 20;  
const int pinSonidoAnalogico =8;

DHT dht(dhtsens, DHT11);		// creacion del objeto, cambiar segundo parametro
				// por DHT11 si se utiliza en lugar del DHT22
void setup(){
  Serial.begin(9600);		// inicializacion de monitor serial
  dht.begin();			// inicializacion de sensor
}

void loop(){

  //mq2
  gas = analogRead(MQ2_PIN);	


  //dht 11
  TEMPERATURA = dht.readTemperature();	// obtencion de valor de temperatura
  HUMEDAD = dht.readHumidity();		// obtencion de valor de humedad

  int valorSonido = analogRead(pinSonidoAnalogico);
  if (valorSonido > umbralSonido) {
    Serial.print("Sonido detectado: ");
    Serial.println(valorSonido);
  }
  Serial.print("{\"gas\":");
  Serial.print(gas);
  Serial.print(" ,\"HUMEDAD\":");
  Serial.print(HUMEDAD);
  Serial.print(" ,\"TEMPERATURA\":");
  Serial.print(TEMPERATURA);
  Serial.println("}");
delay(1000);
}
