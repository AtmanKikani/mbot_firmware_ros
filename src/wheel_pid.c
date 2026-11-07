#include "wheel_pid.h"
static float clampf(float x, float lo, float hi) { return x < lo ? lo : (x > hi ? hi : x); }

void wheel_pid_reset(wheel_pid_t* p) { p->integ = 0.0f; p->dterm = 0.0f; p->e_prev = 0.0f; }

void wheel_pid_set_gains(wheel_pid_t* p, float kp, float ki, float kd, float tf) {
    if (tf <= p->dt / 2.0f) tf = p->dt / 2.0f + 1e-6f;   /* same stability limit RCLib enforces */
    p->kp = kp; p->ki = ki; p->kd = kd; p->tf = tf;
}

void wheel_pid_init(wheel_pid_t* p, float kp, float ki, float kd, float tf, float dt) {
    p->dt = dt; p->out_min = -1.0f; p->out_max = 1.0f;
    wheel_pid_set_gains(p, kp, ki, kd, tf);
    wheel_pid_reset(p);
}

float wheel_pid_step(wheel_pid_t* p, float e) {
    /* forward Euler, identical to RCLib: I[n] = I[n-1] + ki*dt*e[n-1],
       D[n] = (1 - dt/Tf) D[n-1] + (kd/Tf)(e[n] - e[n-1]) */
    float i_new = p->integ + p->ki * p->dt * p->e_prev;
    float d_new = (1.0f - p->dt / p->tf) * p->dterm + (p->kd / p->tf) * (e - p->e_prev);
    float u_raw = p->kp * e + i_new + d_new;
    /* anti-windup by conditional integration: if the output saturates and the new integral step
       pushes further into that saturation, keep the old integral */
    if ((u_raw > p->out_max && i_new > p->integ) || (u_raw < p->out_min && i_new < p->integ)) {
        i_new = p->integ;
    }
    p->integ  = clampf(i_new, p->out_min, p->out_max);
    p->dterm  = d_new;
    p->e_prev = e;
    return clampf(p->kp * e + p->integ + p->dterm, p->out_min, p->out_max);
}
