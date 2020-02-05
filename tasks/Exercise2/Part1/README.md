# Mutex and Channel basics

### What is an atomic operation?
> An atomic operation is an operation that will/shall be performed from start to end without any breaks or interruptions. Either the entire operation is performed, or it is not performed at all. 

### What is a semaphore?
> A semaphore is a variable or abstract data type used for signaling and control in concurrent programing. One of its purposes is to provide a safe way of sharing resources within a system.

### What is a mutex?
> A mutex is a object owned by a thread (Ownership). The mutex allows only one thread to access a resource at a time.

### What is the difference between a mutex and a binary semaphore?
> They are in many ways the same thing, but the use-cases is what differs them. When we are using a mutex, the thread that locked a mutex is supposed to be the only one who can unlock it again. This gives the mutex some conceptual use-case advantages.

### What is a critical section?
> A critical section is a part of a program process that can not be executed at the same time as a critical section of another process.

### What is the difference between race conditions and data races?
 > Race condition -- A flaw that occurs when the timing or ordering of events affects a program’s correctness.
   Data race -- When we have two memory accesses that meets these conditions:
   1) Access the same memory location.
   2) Are performed concurrently by two threads.
   3) Both are not read-operations.
   4) Are not synchronized.
   
   Many race conditions are caused by data races, but not necessarily.

### List some advantages of using message passing over lock-based synchronization primitives.
> You are not as vulnerable to race conditions and deadlocks when you do not use the shared memory-concept. It is also easier to achieve higher performance with message passing.

### List some advantages of using lock-based synchronization primitives over message passing.
> It is easier to achieve correctness with a lock-based synchronization system.
