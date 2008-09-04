#include <stdio.h>
#include <string.h>
#include <time.h>
#include <signal.h>
#include <stdlib.h>
#include <pthread.h> 

long AtomicCompareExchange(long* atomicvar,long compared, long exchange)
{
    return __sync_val_compare_and_swap(atomicvar, compared, exchange);
}

//long AtomicExchange(long* atomicvar,long exchange)
//{
//    return __sync_lock_test_and_set(atomicvar, exchange);
//}

void PLC_GetTime(IEC_TIME *CURRENT_TIME)
{
    clock_gettime(CLOCK_REALTIME, CURRENT_TIME);
}

void PLC_timer_notify(sigval_t val)
{
    PLC_GetTime(&__CURRENT_TIME);
    __run();
}

timer_t PLC_timer;

void PLC_SetTimer(long long next, long long period)
{
    struct itimerspec timerValues;
	/*
	printf("SetTimer(%lld,%lld)\n",next, period);
	*/
    memset (&timerValues, 0, sizeof (struct itimerspec));
	{
#ifdef __lldiv_t_defined
		lldiv_t nxt_div = lldiv(next, 1000000000);
		lldiv_t period_div = lldiv(period, 1000000000);
	    timerValues.it_value.tv_sec = nxt_div.quot;
	    timerValues.it_value.tv_nsec = nxt_div.rem;
	    timerValues.it_interval.tv_sec = period_div.quot;
	    timerValues.it_interval.tv_nsec = period_div.rem;
#else
	    timerValues.it_value.tv_sec = next / 1000000000;
	    timerValues.it_value.tv_nsec = next % 1000000000;
	    timerValues.it_interval.tv_sec = period / 1000000000;
	    timerValues.it_interval.tv_nsec = period % 1000000000;
#endif
	}	
    timer_settime (PLC_timer, 0, &timerValues, NULL);
}
//
void catch_signal(int sig)
{
//  signal(SIGTERM, catch_signal);
  signal(SIGINT, catch_signal);
  printf("Got Signal %d\n",sig);
  exit(0);
}

int startPLC(int argc,char **argv)
{
    struct sigevent sigev;
    /* Translate PLC's microseconds to Ttick nanoseconds */
    Ttick = 1000000 * maxval(common_ticktime__,1);
    
    memset (&sigev, 0, sizeof (struct sigevent));
    sigev.sigev_value.sival_int = 0;
    sigev.sigev_notify = SIGEV_THREAD;
    sigev.sigev_notify_attributes = NULL;
    sigev.sigev_notify_function = PLC_timer_notify;

    timer_create (CLOCK_REALTIME, &sigev, &PLC_timer);
    if(  __init(argc,argv) == 0 ){
        PLC_SetTimer(Ttick,Ttick);
        
        /* install signal handler for manual break */
//        signal(SIGTERM, catch_signal);
        signal(SIGINT, catch_signal);
    }else{
        return 1;
    }
    return 0;
}

static int __debug_tick;

static pthread_mutex_t wait_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t wait_cond = PTHREAD_COND_INITIALIZER;

void AbortDebug()
{
    /* Eventually unlock debugger thread*/
    __debug_tick = -1;
    //pthread_mutex_lock(&wait_mutex);
    pthread_cond_broadcast(&wait_cond);
    //pthread_mutex_unlock(&wait_mutex);
}

int stopPLC()
{
    /* Stop the PLC */
    PLC_SetTimer(0,0);
    timer_delete (PLC_timer);
    __cleanup();
    AbortDebug();
}

extern int __tick;
/* from plc_debugger.c */
int WaitDebugData()
{
    /* Wait signal from PLC thread */
    pthread_mutex_lock(&wait_mutex);
    pthread_cond_wait(&wait_cond, &wait_mutex);
    pthread_mutex_unlock(&wait_mutex);
    return __debug_tick;
}
 
/* Called by PLC thread when debug_publish finished
 * This is supposed to unlock debugger thread in WaitDebugData*/
void InitiateDebugTransfer()
{
    /* signal debugger thread to continue*/
    __debug_tick = __tick;
    //pthread_mutex_lock(&wait_mutex);
    pthread_cond_broadcast(&wait_cond);
    //pthread_mutex_unlock(&wait_mutex);
}
