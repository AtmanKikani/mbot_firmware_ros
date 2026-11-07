#ifndef WHEEL_PID_H
#define WHEEL_PID_H
/* Wheel-velocity PID in standard (non-incremental) form, u = kp*e + I + D, with derivative
 * roll-off and anti-windup. It controls wheel SPEED, exactly like the RCLib filter it replaces.
 * With no saturation it reproduces rc_filter_pid(kp,ki,kd,Tf,dt) exactly (same forward-Euler
 * discretization), so the shipped defaults behave as before. The clamp is applied only to the
 * returned value; no clamped value is ever fed back into the state. */
typedef struct {
    float kp, ki, kd, tf, dt, out_min, out_max;
    float integ;    /* I[n-1] */
    float dterm;    /* D[n-1] */
    float e_prev;   /* e[n-1] */
} wheel_pid_t;

void  wheel_pid_init(wheel_pid_t* p, float kp, float ki, float kd, float tf, float dt);
void  wheel_pid_set_gains(wheel_pid_t* p, float kp, float ki, float kd, float tf);
void  wheel_pid_reset(wheel_pid_t* p);
float wheel_pid_step(wheel_pid_t* p, float e);
#endif
