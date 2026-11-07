#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <rc/math/filter.h>  /* from the firmware repo: -I rc/include */
#include "wheel_pid.h"
/* 1) Unsaturated: wheel_pid must equal rc_filter_pid (no saturation) for random gains and errors.
   2) Saturating step: show RCLib vs wheel_pid outputs for the documented sequences. */
int main(void){
    srand(1); double worst = 0;
    for (int trial = 0; trial < 2000; trial++){
        float kp = (rand()%1000)/1000.0f, ki = (rand()%2)? (rand()%1000)/250.0f : 0.0f,
              kd = (rand()%2)? (rand()%1000)/20000.0f : 0.0f, tf = 0.02f + (rand()%1000)/2000.0f;
        rc_filter_t f = rc_filter_empty(); rc_filter_pid(&f, kp, ki, kd, tf, 0.01);
        wheel_pid_t p; wheel_pid_init(&p, kp, ki, kd, tf, 0.01f); p.out_min = -1e9f; p.out_max = 1e9f;
        for (int n = 0; n < 400; n++){
            float e = ((rand()%2001) - 1000)/100.0f;
            double a = rc_filter_march(&f, e), b = wheel_pid_step(&p, e);
            double rel = fabs(a-b)/(1.0+fabs(a)); if (rel > worst) worst = rel;
        }
        rc_filter_free(&f);
    }
    printf("unsaturated equivalence, worst relative diff over 2000x400 steps: %.2e\n", worst);
    const double e1[] = {16,16,16,15.66,15.5,14.83,14.66,14.15,14.15,14.15};
    rc_filter_t f = rc_filter_empty(); rc_filter_pid(&f,0.6,0.05,0,0.1,0.01); rc_filter_enable_saturation(&f,-1,1);
    wheel_pid_t p; wheel_pid_init(&p,0.6f,0.05f,0.0f,0.1f,0.01f);
    printf("PI step  RCLib:"); for(int i=0;i<10;i++) printf(" %6.3f", rc_filter_march(&f,e1[i])); printf("\n");
    printf("PI step  fixed:"); for(int i=0;i<10;i++) printf(" %6.3f", wheel_pid_step(&p,e1[i])); printf("\n");
    rc_filter_free(&f);
    f = rc_filter_empty(); rc_filter_pid(&f,0.2,1.0,0.01,0.1,0.01); rc_filter_enable_saturation(&f,-1,1);
    wheel_pid_init(&p,0.2f,1.0f,0.01f,0.1f,0.01f);
    printf("PID e=10 RCLib:"); for(int i=0;i<6;i++) printf(" %6.3f", rc_filter_march(&f,10)); printf("\n");
    printf("PID e=10 fixed:"); for(int i=0;i<6;i++) printf(" %6.3f", wheel_pid_step(&p,10)); printf("\n");
    return 0;
}
