# p4_timecop [![Coverage Status](https://coveralls.io/repos/github/rmaffesoli/p4_timecop/badge.svg?branch=main)](https://coveralls.io/github/rmaffesoli/p4_timecop?branch=main)
A utility to automatic unlock files that have been locked longer than a set duration.
This can run server or client side, wherever you prefer.

## Requirements
- Python 3
- p4python package (pip installable)

## Basic Operation
```
PS E:\repos\p4_timecop> python e:\repos\p4_timecop\kernel\run_timecop.py -h
usage: run_timecop.py [-h] [-c CONFIG] [-t TIMELIMIT] [-d DATA] [-l LOG]

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
  -t TIMELIMIT, --timelimit TIMELIMIT
  -d DATA, --data DATA
  -l LOG, --log LOG

PS E:\repos\p4_timecop> python e:\repos\p4_timecop\kernel\run_timecop.py
Connecting to server:
passwd: None
Password not provided, attempting to use local ticket
Auto Unlock Completed.
```
The script is made to have it's configurable values provided by either a configuration json file, or through argument overrides.
Arguments take precedence over the config file.
While you can run this script manually, it's more expected that you'll be running it hourly via either a cron table job or through the windows task scheduler.

## config.json
Within the config file you can define the server connection you're trying to make. if no password is provided the system will attempt to use any existing tickets for the given user that are on the local machine.

The `file_lock_time_limit` value is in a `Day:Hour:Minute:Second` format with the default value of 1 day used if noting is provided.

If you'd prefer to have certain users or groups be exept from the unlocking procedures you can define with users/groups are to be skipped in the config file as well. 

The filetype_filter is a regex filter to be defined if desired, the default woll only unlock exclusive checkout filetypes (+l). Remove this value if you would prefer it to apply to all file types on the server.


```
{
    "servers":{ 
        "local": {
            "server":{
                "port": "ssl:helix:1666",
                "user": "rmaffesoli",
                "password": null,
                "charset": "none"
            },
            "file_lock_time_limit": "01:00:00:00",
            "log_filepath": "../log.txt",
            "data_filepath": "../data.json",
            "ignored_usernames": ["username"],
            "ignored_groupnames": ["groupname"],
            "filetype_filter": "\\+[^l]*l"
        }
    }
}

```

## log.txt
Basic logging will occur to register the script being run as well as any files that have been unlocked with the process.
```
Tue Feb 20 20:18:27 2024: Auto Unlock Completed.
Tue Feb 20 20:25:00 2024: //demo_interiors_stream/props/mainline/bookshelf.fbx has been force reverted from rmaffesoli@rmaffesoli_mafflow_mainline_243.
Tue Feb 20 20:25:00 2024: Auto Unlock Completed.
```

## data.json
Upon the script running, it will first load the previous open data that was gathered at the time of the last run.
```
{
    "//demo_interiors_stream/library/mainline/library.fbx": [
        {
            "type": "binary",
            "client": "local_lib",
            "user": "rmaffesoli",
            "timestamp": "Tue Feb 20 19:18:25 2024"
        }
    ]
}
```

## ToDo items?:
- [X] Full Test Coverage
- [X] Compiled executables
