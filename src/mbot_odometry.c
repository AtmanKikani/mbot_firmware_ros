#include "mbot_odometry.h"
#include <math.h>

#ifndef PI
#define PI 3.14159265358979323846f
#endif

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
    // Use the IMU instead of the wheel-derived angular velocity
    (void)wz;

    // Estimate heading halfway through the time interval
    float theta_mid = *theta + 0.5f * gyro_z * dt;

    // Integrate forward velocity in the world frame
    *x += (vx * cosf(theta_mid) - vy * sinf(theta_mid)) * dt;
    *y += (vx * sinf(theta_mid) + vy * cosf(theta_mid)) * dt;

    // Integrate gyroscope angular velocity
    *theta += gyro_z * dt;

    // Normalize heading to [-pi, pi]
    while (*theta > PI)  *theta -= 2.0f * PI;
    while (*theta <= -PI) *theta += 2.0f * PI;
    return;
}