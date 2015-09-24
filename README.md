# Clockwork
Scheduler for shell jobs coded by python2

## Feature
##### Crontab Style Trigger

[* * * * *] five place-holders meaning [minute hour day month weekday]

Possible value support:
  * * means everything
  * */2 means every 2 units
  * Positive integer means specific value

##### Shell Command with Reserve Word

Command can contain reserved words like TODAY,YESTERDAY. These words are represent use specified format:#{ReservedWord}. When
extract real command from job, these reserved words will be replaced.

##### SSH Linker

To execute remote shell command,we use the capacity of ssh itself, ssh host 'cmd1;cmd2'.Once user assign host,we generate this command.

##### Job Dependence

One job could depend on others.When needed, user should set the job depend on,and a structure of delta time:deltaDay, deltaHour, deltaMinute.Every unit accepted a negative integer if this unit is ignored,or TaskRunner will subtract this value by execute time of a task to tell if a depended task has been successfully executed. 

## Start Server
* Using doc/sql/create.sql to create tables
* install required modules in requirements.txt
* Edit configurations in conf/server.py
* Add clockwork to PYTHONPATH
* python2.7 server.py

## Start Clinet
* Add clockwork to PYTHONPATH
* python2.7 client/client.py 127.0.0.1 3993 

