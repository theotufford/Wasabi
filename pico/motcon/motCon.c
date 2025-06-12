#include <stdio.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "pico/binary_info.h"
#include "pico/time.h"
#include <string.h>
#include <math.h>

typedef struct motorStruct {
  int target; // stores target position
  int position; // stores initial pre-move position
  int stepCount; // stores number of steps in current move
  int stepsPerRev;// steps/revolution
  int stepsPer_mm;
  int stepPin;
  int dirPin;
  int limitSwitchPin;
  int mindelay;
  float vMax; 
  float accel;
} Motor;

typedef struct pumpStruct {
  float stepsPer_ul; //pretty much esteps
  int target;
  int position;
  int stepPin;
  int dirPin;
  char* contents;
  // everything else is handled by the translator
} Pump;

typedef struct MachineStruct{ // parent struct for storing all the motors and other info about the machine
  // dimensions
  float armLength;
  float handLength;
  float spacing;
  // working volume bounding box
  int xMax;
  int xMin;
  int yMax;
  int yMin;
  int zMax;
  int zMin;
  // pointers to motors
  Motor* aMot;
  Motor* bMot;
  Motor* zMot;
  // work offset values
  float X0;
  float Y0;
  float Z0;
  int pumpCount;
  Pump** pumps;
} Machine;


void step(Motor* mot){
  printf("attempting to step\n");
  gpio_put(mot->stepPin, 1);
  sleep_us(1);
  gpio_put(mot->stepPin, 0);
}
void stepPump(Pump* mot){
  gpio_put(mot->stepPin, 1);
  sleep_us(1);
  gpio_put(mot->stepPin, 0);
}
float degrees(float rads){
  return ((360*rads)/(2*M_PI));
}

int solve5bar(Machine machine, char* position) {
  // takes an input of a string of form "<gcode id> X:<x position> Y:<y position> Z:<z position>"
  printf("%s\n", position);
  float x;
  float y;
  float z;
  int success = sscanf(position, "G0 X:%f Y:%f Z:%f\n", &x, &y, &z);
  if (success == 0){
    return -1; // handle poorly formatted data
  }
  printf("x:%f, y:%f, z:%f\n", x,y,z);
//  x += machine.X0;
//  y += machine.Y0;
//  z += machine.Z0;
  float thetaR; // right motor angle
  float thetaL; // left motor angle 
  float A = machine.armLength;
  float H = machine.handLength;
  float D = machine.spacing;
  float b_R = D/2 - x; // distance of x coord from the origin of the right limb
  float b_L = D/2 + x; // distance of x coord from the origin of the left limb
  float d_R = sqrt(b_R*b_R + y*y); // length of segment connecting the end coord and the right limb origin
  float d_L = sqrt(b_L*b_L + y*y);// length of segment connecting the end coord and the left limb origin
  //  the sum of the internal angle of the right triangle with d_(L|R) as its hypotenuse and the and the angle between d_(L|R) and the positive 
  //  solution of the intersection between a circle of radius H centered at the end point and and a circle of radius A 
  //  centered at the joint origin
  // solutions for the negative component of d_(R|L) (because it is a sqrt so technically it has a +- in front of it) 
  // needs to be adjusted by 180 to fit the correct solution for some reason and I dont really feel like I need to figure out why
  thetaR = acos( d_R/A - (d_R*d_R-A*A+H*H)/(2*d_R*A) ) + asin(y/d_R);
  if (x>(machine.spacing/2)){
    thetaR = acos( d_R/A - (d_R*d_R-A*A+H*H)/(2*d_R*A) ) - asin(y/d_R) + M_PI;
  } 
  thetaL = acos(d_L/A - (d_L*d_L-A*A+H*H)/(2*d_L*A) ) + asin(y/d_L);
  if (x < -machine.spacing/2){
    thetaL = acos(d_L/A - (d_L*d_L-A*A+H*H)/(2*d_L*A) ) - asin(y/d_L) + M_PI;
  }
  printf("theta_l:%f\ntheta_r:%f\n", thetaL, thetaR);

  machine.aMot -> target = (thetaL / (2*M_PI/(float)(machine.aMot -> stepsPerRev)) );
  machine.bMot -> target = (thetaR / (2*M_PI/(float)(machine.bMot -> stepsPerRev)) );

//  machine.zMot -> target = (z / (float)(machine.zMot -> stepsPer_mm));
}
int dispenseAnalytes(Machine machine, char* inputData){
  char *volumes = strchr(inputData, ' ');
  volumes++;
  char* tok = strtok(volumes, " :");
  while (tok != NULL) {  
    int targetPumpIndex;
    int found;
    for (int i=0; i < machine.pumpCount; i++){
      char* pumpAnalyte = machine.pumps[i] -> contents;
      if (strcmp(pumpAnalyte, tok) == 0){
        tok = strtok(NULL, " :");
        float volume;
        sscanf(tok,"%f", &volume); 
        machine.pumps[i] -> target = volume*(machine.pumps[i] -> stepsPer_ul);
        found = 1;
      }
    } if (found == 0){
      printf("formatting error, analyte \"%s\" not found\n...\naborting\n", tok);
      tok = strtok(NULL, " :");
      return -1;
    }
    tok = strtok(NULL, " :");
  }
  int delay = 1500;
  while(1){
    for (int i=0; i < machine.pumpCount; i++){
      if (machine.pumps[i] -> target != machine.pumps[i] -> position){
        stepPump(machine.pumps[i]);
      } else if ( i + 1 == machine.pumpCount){
        break;
      }
    }
    delay -= 10;
    if (delay < 400){
      delay = 400;
    }
    sleep_us(delay);
  }
}

     
int main() {
  stdio_init_all();
  while (1){
    printf("hi");
    sleep_us(200);
  }

  /*
    TODO: instead of this being done manually, there should be a function that 
   interacts with the python end to populate these automatically from a config file, 
   possibly editable via web interface
  */
  Motor driver1;
  driver1.target = 0;
  driver1.position = 0;
  driver1.stepsPerRev = 200;
  driver1.limitSwitchPin = 20;
  driver1.stepPin = 2;
  driver1.dirPin = 3;
  driver1.vMax = 40;
  driver1.accel = 1.5;

  Motor driver2;
  driver2.target = 0;
  driver2.position = 0;
  driver2.stepsPerRev = 200;
  driver2.limitSwitchPin = 20;
  driver2.stepPin = 6;
  driver2.dirPin = 7;
  driver2.vMax = 40;
  driver2.accel = 1.5;

  Pump driver3;
  driver3.target = 0;
  driver3.position = 0;
  driver3.stepsPer_ul = 3;
  driver3.contents = "D2.0R";
  driver3.stepPin = 4;
  driver3.dirPin = 5;


  Pump* pumpArray[] = {&driver3};

  Machine wasabi;
  wasabi.armLength = 30;
  wasabi.handLength = 50;
  wasabi.spacing = 45;
  wasabi.aMot = &driver1;
  wasabi.bMot = &driver2;
  wasabi.pumps = pumpArray;
  wasabi.pumpCount = 1;



  /*TODO implement recursive pin activation
   */
  gpio_init(wasabi.aMot -> stepPin);
  gpio_init(wasabi.aMot -> dirPin);
  gpio_init(wasabi.bMot -> stepPin);
  gpio_init(wasabi.bMot -> dirPin);
  gpio_init(driver3.stepPin);
  gpio_init(driver3.dirPin);

  gpio_set_dir(wasabi.aMot -> stepPin, GPIO_OUT);
  gpio_set_dir(wasabi.aMot -> dirPin, GPIO_OUT);
  gpio_set_dir(wasabi.bMot -> stepPin, GPIO_OUT);
  gpio_set_dir(wasabi.bMot -> dirPin, GPIO_OUT);
  gpio_set_dir(driver3.stepPin, GPIO_OUT);
  gpio_set_dir(driver3.dirPin, GPIO_OUT);
  // main control loop
  char inputBuf[64];
  while (1) {
    printf("serial working\n");
    fgets(inputBuf, sizeof(inputBuf), stdin);
    printf("%s\n", inputBuf);
    char* cleanedInput = strtok(inputBuf, "$");
    char code[5];
    sscanf(cleanedInput, "%s", code);
    printf("cleaned input: %s\n", cleanedInput);

    if (strcmp(code, "G0") == 0){
      printf("a target:%d a position:%d\n", wasabi.aMot -> target, wasabi.aMot -> position);
      printf("b target:%d b position:%d\n", wasabi.bMot -> target, wasabi.bMot -> position);
      solve5bar(wasabi, cleanedInput);
      printf("a target:%d a position:%d\n", wasabi.aMot -> target, wasabi.aMot -> position);
      printf("b target:%d b position:%d\n", wasabi.bMot -> target, wasabi.bMot -> position);

      //set directions
      int adir = 1; 
      int bdir = 1;
      if (wasabi.aMot -> target - wasabi.aMot ->position < 0){
        adir = -1;
        gpio_put(wasabi.aMot -> dirPin, 0);
      }
      if (wasabi.bMot -> target - wasabi.bMot ->position < 0){
        bdir = -1;
        gpio_put(wasabi.bMot -> dirPin, 0);
      }

      // start initial move timer 
      uint64_t startTime = time_us_64();
      printf("startTime %llu\n", startTime);
      while(1){
        printf("hi\n");
        uint64_t time = time_us_64() - startTime;
        if ( wasabi.aMot -> target == wasabi.aMot -> position) {
          if ( wasabi.bMot -> target == wasabi.bMot -> position ){
            break; // break if both motors are at position
          } else { //control b motor 
            int delay = 1/ (wasabi.bMot -> stepsPerRev*wasabi.bMot ->accel*time / 2*M_PI*1000*1000);
            printf("in b loop");
            if (delay< wasabi.bMot -> mindelay){
              delay = wasabi.bMot -> mindelay;
            }
            sleep_us(delay);
            step(wasabi.bMot);
            wasabi.bMot -> position += 1*bdir;
          }
        } else if (wasabi.bMot -> target == wasabi.bMot -> position){ // control a motor 
          int delay = 1/ (wasabi.aMot -> stepsPerRev*wasabi.aMot ->accel*time / 2*M_PI*1000*1000);
          printf("in a loop\n");
          if (delay< wasabi.aMot -> mindelay){
            delay = wasabi.aMot -> mindelay;
          }
          printf("var = %d\n", delay);
          sleep_us(delay);
          step(wasabi.aMot);
          wasabi.aMot -> position += 1*adir;
        } else { // control both motors

          int delayA = 1/ (wasabi.aMot->stepsPerRev*wasabi.aMot->accel*time / 2*M_PI*1000*1000);
          int delayB = 1/ (wasabi.bMot->stepsPerRev*wasabi.bMot->accel*time / 2*M_PI*1000*1000);

          if (delayA< wasabi.aMot -> mindelay){
            delayA = wasabi.aMot -> mindelay;
          }

          if (delayB< wasabi.bMot -> mindelay){
            delayB = wasabi.bMot -> mindelay;
          }

          printf("in dual loop: \n a:%d\nb:\n-----", delayA, delayB);

          if (delayA>delayB){
            sleep_us(delayB);
            step(wasabi.bMot);
            sleep_us(delayA-delayB);
            step(wasabi.aMot);
          } else if (delayB>delayA){
            sleep_us(delayA);
            step(wasabi.bMot);
            sleep_us(delayB-delayA);
            step(wasabi.aMot);
          } else {
            sleep_us(delayA);
            step(wasabi.bMot);
            step(wasabi.aMot);
          }
          wasabi.aMot -> position += adir;
          wasabi.bMot -> position += bdir;
        }
      } 
    } else if (strcmp(code, "P0") == 0){
      //      printf("sending input to volume solver: '%s'\n", cleanedInput);
      dispenseAnalytes(wasabi, cleanedInput);
    }
    printf("drivers:%d, ", driver1.target);
    printf("%d, ", driver2.target);
    printf("%d, ", driver3.target);

  }

}
// depreciated movement and control code to be integrated with Gcode interpretation
//        if (sscanf(inputBuf, "%d", &steps) == 1){
////          printf("targeted %d steps\n", steps);
//          if (steps > 0 ){
//            gpio_put(DIR_PIN, 1);
//          } else {
//            gpio_put(DIR_PIN, 0);
//          }
//          steps = abs(steps);
//
//          while ( stepCount <= steps ){
//            gpio_put(STP_PIN, 1);
//            sleep_us(2);
//            gpio_put(STP_PIN, 0);
//            sleep_us(delay);
//            stepCount++;
//            if (delay < 1000){
//              delay-=10;
//            }
//          } 
//        } else {
////          printf("%s is not a valid int\n", inputBuf);
//        }
//
//      } else {
////        printf("fgets fail\n");
//      }

//}
