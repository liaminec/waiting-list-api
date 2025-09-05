# Notes and improvements

### 1- Why was it not dockerized ?

I wish I could have, I love Docker. The problem is that I work on a 2017 
MacBook Air, which cannot reach MacOS 13.0 (it is not compatible).

And here is the problem, Docker has dropped support for MacOS versions 
under 13.0, so no Docker for me.

### 2- Why Sqlite ?

It went with the impossibility to dockerize. I would rather have used Postgres 
or at least MySQL, but without Docker, I felt like it would have complicated 
things 

### 3- Why FastAPI and SQLModel

I used FastAPI rather than Django to remain consistent with the stack.
As for SQLModel with alembic, I wanted to get a measure on the difficulty of
using an ORM with FastAPI and wanted to give the possibility of tracking the 
evolution of the DB.

### 4- Missing unit tests ?

It was a deliberate choice to omit unit tests for simple features that are
a bit out of the scope of the exercise, to gain time. However, the more 
important and complex features are very much tested. Hopefully this will show 
my ability to test

### 5- Possible improvement: EDA

Since the logic is time sensitive and prone to problems of concurrency, 
one possible improvement would be to put the logic of creation of participations
(confirmed, in waiting list, or pending) as a task triggered by an event sent 
by the view to a queue (For example with RabbitMQ + Celery).



