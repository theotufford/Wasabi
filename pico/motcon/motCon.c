#include <stdio.h>
#include <pthread.h>
#include "hardware/sync.h"
#include <stdlib.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "pico/binary_info.h"
#include "pico/time.h"
#include <string.h>
#include <math.h>

volatile int moving;

typedef struct motorStruct {
  int stepPin;
  int dirPin;
  int limitSwitchPin;
  int stepsPerRev;// steps/revolution
  int stepsPer_mm;
  volatile int target; // stores target position
  volatile int livePosition; // stores initial pre-move position
  volatile int staticPosition;
  int increment;
  float vMax;
  float accel;
  uint64_t initialMoveTime;
  float accelStop;
  float constStop;
  float endTime;
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

struct machine { // parent struct for storing all the motors and other info about the machine
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
};

struct machine wasabi;

void step(Motor* mot){
  gpio_put(mot->stepPin, 1);
  sleep_us(3);
  gpio_put(mot->stepPin, 0);
  mot-> livePosition += mot-> increment;
}

uint64_t getStepTiming(Motor* mot){
  float Q = (2*M_PI/mot->stepsPerRev)*abs(mot -> target - mot -> staticPosition); // gets the total distance of the move in rads
  float theta = ((2*M_PI/mot->stepsPerRev) * (abs(mot -> livePosition - mot-> staticPosition) + 1));
  float stepTiming;
  if(mot -> livePosition == mot -> target){
    mot -> staticPosition = mot->livePosition;
    return 0;
  }
  if (theta < mot -> accelStop ){
    stepTiming =  sqrt((2*theta)/mot -> accel);
  } else if (theta < mot -> constStop){
    stepTiming = (theta/mot->vMax) + (mot->vMax/(2*mot->accel));
  } else {
    stepTiming = mot -> endTime - sqrt((2*(Q-theta))/mot->accel);
  }
  uint64_t step_us = (uint64_t)(stepTiming * 1e6f) + mot-> initialMoveTime; 
  return step_us;
}

absolute_time_t motor_callback(Motor* mot){
    step(mot);
    absolute_time_t next_time = getStepTiming(mot);
    return next_time;
}
void aCallback(){
  absolute_time_t next = motor_callback(wasabi.aMot);
  if(next == 0){
    hardware_alarm_unclaim(0);
    return;
  } else{
    if (hardware_alarm_set_target(0, next) == 1){
      aCallback();
    }
  }
}
void bCallback(){
  absolute_time_t next = motor_callback(wasabi.bMot); // call the stepping function and get the timing of the next move
  if(next == 0){ // if at position
    hardware_alarm_unclaim(1); // free the alarm from the function
    return;
  } else{
    if (hardware_alarm_set_target(1, next) == 1){
      bCallback();
    }
  }
}

uint64_t initializeMove(Motor* mot){
  float Q = (2*M_PI/mot->stepsPerRev)*fabs((float)(mot -> target - mot -> staticPosition)); // gets the total distance of the move in rads
  float s = (Q/2) - ((mot->vMax*mot->vMax)/mot->accel); // positive if the motor will reach max v before hitting the halfway point
  float v = mot->vMax;
  if (s<=0){
    v = sqrt(Q*mot->accel);
  }
  mot -> accelStop = (v*v)/(2*mot->accel); 
  mot -> constStop = (Q - (v*v)/(2*mot->accel)); 
  mot -> endTime = (Q/v + v/mot->accel);
  printf("accelStop: %lf\n", mot-> accelStop);
  printf("constStop: %lf\n", mot-> constStop);
  uint64_t start_us = time_us_64()+20000;
  mot->initialMoveTime = start_us;
  moving += 1;
  return 0;
}

void stepPump(Pump* mot){
  gpio_put(mot->stepPin, 1);
  sleep_us(1);
  gpio_put(mot->stepPin, 0);
}
float degrees(float rads){
  return ((360*rads)/(2*M_PI));
}

int solve5bar(char* position) {
  // takes an input of a string of form "<gcode id> X:<x position> Y:<y position> Z:<z position>"
  printf("%s\n", position);
  float x;
  float y;
  float z;
  int success = sscanf(position, "G0 X:%f Y:%f Z:%f\n", &x, &y, &z);
  if (success == 0){
    printf("data formatting failed, exiting\n");
    return -1; // handle poorly formatted data
  }
  printf("x:%f, y:%f, z:%f\n", x,y,z);
//  x += wasabi.X0;
//  y += wasabi.Y0;
//  z += wasabi.Z0;
  float thetaR; // right motor angle
  float thetaL; // left motor angle 
  float A = wasabi.armLength;
  float H = wasabi.handLength;
  float D = wasabi.spacing;
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
  if (x>(wasabi.spacing/2)){
    thetaR = acos( d_R/A - (d_R*d_R-A*A+H*H)/(2*d_R*A) ) - asin(y/d_R) + M_PI;
  } 
  thetaL = acos(d_L/A - (d_L*d_L-A*A+H*H)/(2*d_L*A) ) + asin(y/d_L);
  if (x < -wasabi.spacing/2){
    thetaL = acos(d_L/A - (d_L*d_L-A*A+H*H)/(2*d_L*A) ) - asin(y/d_L) + M_PI;
  }
  printf("R:%f, L:%f\n", thetaL, thetaR);

  wasabi.aMot -> target = (thetaL / (2*M_PI/(float)(wasabi.aMot -> stepsPerRev)) );
  wasabi.bMot -> target = (thetaR / (2*M_PI/(float)(wasabi.bMot -> stepsPerRev)) );

  //wasabi.zMot -> target = (z / (float)(wasabi.zMot -> stepsPer_mm));
}
int dispenseReagent(char* inputData){
  char *volumes = strchr(inputData, ' ');
  volumes++;
  char* tok = strtok(volumes, " :");
  while (tok != NULL) {  
    int targetPumpIndex;
    int found;
    for (int i=0; i < wasabi.pumpCount; i++){
      char* pumpReagent= wasabi.pumps[i] -> contents;
      if (strcmp(pumpReagent, tok) == 0){
        tok = strtok(NULL, " :");
        float volume;
        sscanf(tok,"%f", &volume); 
        wasabi.pumps[i] -> target = volume*(wasabi.pumps[i] -> stepsPer_ul);
        found = 1;
      }
    } if (found == 0){
      printf("formatting error, Reagent\"%s\" not found\n...\naborting\n", tok);
      tok = strtok(NULL, " :");
      return -1;
    }
    tok = strtok(NULL, " :");
  }
  int delay = 1500;
  while(1){
    for (int i=0; i < wasabi.pumpCount; i++){
      if (wasabi.pumps[i] -> target != wasabi.pumps[i] -> position){
        stepPump(wasabi.pumps[i]);
      } else if ( i + 1 == wasabi.pumpCount){
        break;
      }
    }
    delay -= 10;
    if (delay < 4000){
      delay = 4000;
    }
    sleep_us(delay);
  }
}


     
int main() {
  stdio_init_all();
  /*
    TODO: instead of this being done manually, there should be a function that 
   interacts with the python end to populate these automatically from a config file, 
   possibly editable via web interface
  */

  float genAccelValue = 1000.0; // rads/s
  float genVMax = 50.0;

  Motor driver1;
  driver1.stepsPerRev = 200;
  driver1.limitSwitchPin = 20;
  driver1.stepPin = 2;
  driver1.dirPin = 3;
  driver1.vMax = genVMax;
  driver1.accel = genAccelValue;
  driver1.staticPosition = 0;
  driver1.target = 0;

  Motor driver2;
  driver2.stepsPerRev = 200;
  driver2.limitSwitchPin = 20;
  driver2.stepPin = 6;
  driver2.dirPin = 7;
  driver2.vMax = genVMax;
  driver2.accel = genAccelValue;
  driver2.staticPosition = 0;
  driver2.target = 0;

  Pump driver3;
  driver3.stepsPer_ul = 3;
  driver3.contents = "D2.0R";
  driver3.stepPin = 4;
  driver3.dirPin = 1;


  Pump* pumpArray[] = {&driver3};

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
    if(wasabi.aMot -> target != wasabi.aMot -> staticPosition && wasabi.bMot -> target != wasabi.bMot -> staticPosition) {
      //printf("\n--\nA: %d, %d, %d\nB: %d, %d, %d\n--\n", wasabi.aMot-> target, wasabi.aMot-> staticPosition, wasabi.aMot-> livePosition , wasabi.bMot-> target, wasabi.bMot-> staticPosition, wasabi.bMot-> livePosition);
      printf("moving\n");
      continue;
    }
    else{
      printf("not moving\n");
      fgets(inputBuf, sizeof(inputBuf), stdin);
      printf("%s\n", inputBuf);
      char* cleanedInput = strtok(inputBuf, "$");
      char code[5];
      sscanf(cleanedInput, "%s", code);
      printf("cleaned input: %s\n", cleanedInput);
      if (strcmp(code, "G0") == 0){
        solve5bar(cleanedInput);
        //set directions
        wasabi.aMot -> increment = 1;
        wasabi.bMot -> increment = 1;
        gpio_put(wasabi.aMot -> dirPin, 1);
        gpio_put(wasabi.bMot -> dirPin, 1);
        if (wasabi.aMot -> target - wasabi.aMot -> staticPosition < 0){
          gpio_put(wasabi.aMot -> dirPin, 0);
          wasabi.aMot -> increment = -1;
        } 
        if (wasabi.bMot -> target - wasabi.bMot ->staticPosition < 0){
          gpio_put(wasabi.bMot -> dirPin, 0);
          wasabi.bMot -> increment = -1;
        }
        hardware_alarm_claim(0);
        hardware_alarm_claim(1);
        hardware_alarm_set_callback(0, (hardware_alarm_callback_t) aCallback);
        hardware_alarm_set_callback(1, (hardware_alarm_callback_t) bCallback);
        initializeMove(wasabi.bMot);
        initializeMove(wasabi.aMot);
        aCallback();
        bCallback();

      } else if (strcmp(code, "P0") == 0){
        //      printf("sending input to volume solver: '%s'\n", cleanedInput);
        dispenseReagent(cleanedInput);
      } 
    }
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
