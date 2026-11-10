#include "mbot_odometry.h"
#include <math.h>

#ifndef PI
#define PI 3.14159265358979323846f
#endif
//Threshold for switching to the gyro, in rad/s (starting guess, tune on the robot)
#define GYRO_THRESHOLD 0.1f 

void mbot_calculate_odometry(float vx, float vy, float wz, float dt, float* x, float* y, float* theta) {
    // Update pose
    *x += vx * dt * cos(*theta) - vy * dt * sin(*theta);
    *y += vx * dt * sin(*theta) + vy * dt * cos(*theta);
    *theta += wz * dt;

    // Normalize theta to [-pi, pi]
    while (*theta > PI) *theta -= 2.0 * PI;
    while (*theta <= -PI) *theta += 2.0 * PI;
}

void mbot_calculate_gyrodometry(float vx, float vy, float wz, float dt, float gyro_z, float* x, float* y, float* theta) {
    // pick the yaw rate: trust the gyro only when it disagrees with the wheels by a lot
    float omega = wz;
    if (fabsf(gyro_z - wz) > GYRO_THRESHOLD) {
        omega = gyro_z;
    } 
    // right now we embed the switch into the gyro+odom calculator, but we can also seperate it as an isolated function.
    // embeddding uses less code, seperating is easier to test, change, debug

    // Update pose (same as mbot_calculate_odometry, but using omega)
    *x += vx * dt * cos(*theta) - vy * dt * sin(*theta);
    *y += vx * dt * sin(*theta) + vy * dt * cos(*theta);
    *theta += omega * dt;

    // Normalize theta to [-pi, pi]
    while (*theta > PI) *theta -= 2.0 * PI;
    while (*theta <= -PI) *theta += 2.0 * PI;

}


