

#include <DHT.h>		// importa la Librerias DHT
#include <DHT_U.h>

#define MQ2_PIN A3   // sensor de gas 
#define sonido_mic 10     // sensor de sonido
#define sens_mic A4
#define LDRPIN 5      //sensor de luz
#define agua_pin A5       // SENSOR DE AGUA 
int dhtsens = 7;			// pin DATA de DHT22 a pin digital 2
int TEMPERATURA;
int HUMEDAD;
int gas;
int agua;
int valor_son;
int sens ;


DHT dht(dhtsens, DHT11);		// creacion del objeto, cambiar segundo parametro
				// por DHT11 si se utiliza en lugar del DHT22
void setup(){
  Serial.begin(9600);		// inicializacion de monitor serial
  dht.begin();			// inicializacion de sensor
}

void loop(){

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

   Serial.print("{\"GAS\":");
  Serial.print(gas);
  Serial.print(" ,\"HUM\":");
  Serial.print(HUMEDAD);
  Serial.print(" ,\"TEM\":");
  Serial.print(TEMPERATURA);
   Serial.print(" ,\"agua\":");
  Serial.print(agua);
  Serial.print(" ,\"Sonido\":");
  if (valor_son == HIGH){
   Serial.print(1); 
  }else{
    Serial.print(0);
  }
  Serial.print(" ,\"Sonido sens\":");
  Serial.print(sens);
  Serial.println("}");

  delay(1000);
}
