BigBrotherBot (B3) management script
====================================

In this directory you can find a BASH script which can help you dealing with B3 on Linux systems.  
In particular 2 BASH scripts needs some more attention:

Such BASH script provides a set of tools which can help you managing your B3 instances on a Linux system.  
They allow you to: 

* Launch multiple B3 instances (as background processes).
* Shutdown gracefully alive B3 instances.
* Monitor the status of your B3 instances (and list the available ones).
* Clean B3 directory from Python compiled sources _(only for the source distribution)_.
* Check for the correct Python interpreter to be available _(only for the source distribution)_.
* Prevent you from running B3 instances as **root**.

### Requirements

* Linux (tested on Debian, Ubuntu)
* [Bash](https://www.gnu.org/software/bash/): usually installed by default
* [bc](https://www.gnu.org/software/bc/manual/html_mono/bc.html) shell command: `apt-get install bc` on Debian based distro
* [Screen](http://linux.die.net/man/1/screen) window manager

In order for B3 to work correctly using this script you need to setup a Linux system user that will run B3. Such user
will have to be proprietory of all the B3 files. If for example your system user is **b3** and belongs to the group **users** 
you can then change ownership of all the B3 files to belong to the **b3** user by typing the following in the Linux console: 
`chown -R b3:users /path/to/main/b3/directory`. For information on how to add a Linux system user, please refer to
the [man page](http://linux.die.net/man/8/useradd).

### How to use

As described above, the script will allow you to launch multiple B3 instances so you can manage multiple game servers.
In order to do that you need to specify multiple B3 configuration files to be used to start B3 instances: those 
configuration files can be placed under the following paths:
 
* Main B3 configuration directory (namely `b3/conf`)
* B3 home directory: if the system user running B3 is **b3**, the B3 home directory will b3 `/home/b3/.b3/`.
 
The names of the configuration files needs to follow a specific pattern: `b3_[<name>].[.ini|.xml]`.  

As an example let's assume you are running **2** game servers and you need to start **2** B3 intances: let's call them 
**tdm** and **ctf**. What you need to do is pretty simple: you need to create **2** configuration files (one for each instance):

* create a `b3_tdm.xml` or `b3_tdm.ini` for the **tdm** instance
* create a `b3_ctf.xml` or `b3_ctf.ini` for the **ctf** instance

*NOTE: you can obviously customize those configuration files as you want hence you can load different plugins and 
different plugin configuration files on every B3 instance you intend to run.*

After saving the configuration files, you are ready to launch your B3 instances using the `b3.sh` script: the script 
autodiscovers new configuration files and let you interact with them by using the chosen B3 instance name as input parameter.
So, in the example above you can launch the **tdm** and **ctf** B3 instances by typing:

* `./b3.sh start tdm`
* `./b3.sh start ctf`

The script will inform you on the result of the startup operation: you can then check the status of the B3 processes
using the `status` command provided by the `b3.sh` script.  
Note that the B3 instance `<name>` parameter is optional: if you do not specify it the script will execute the given 
operation on all the B3 instances it can find (so in the previous example you could have just typed `./b3.sh start` to 
start both the **tdm** and **ctf** B3 instances.

### Commands reference

```bash
-usage: b3.sh  start   [<name>] - start B3
               stop    [<name>] - stop B3
               restart [<name>] - restart B3
               status  [<name>] - display current B3 status
               clean            - clean B3 directory (only for the source distribution)
```

### For advanced users

* You can disable B3 autorestart mode by setting the `B3_AUTORESTART` environment variable to `0` (in the system user 
  `.bash_profile`): after doing so B3 won't restart automatically after a crash.
* You can enable logging by setting the `B3_LOG` environment variable to `1` (in the system user `.bash_profile`): log 
  will be available in `b3/scripts/log/app.log` and will contain the console output produced by the BASH script.
* You can turn off bash colors by setting the `USE_COLORS` variable to `0` (in the BASH script): while the usage is 
  advised for a fast reading and understanding of the console output, some people may not like them.
* If you want to be able to control all your B3 instances no matter the current working directory you can setup an alias
  in your system user `.bash_profile`: `alias b3='/path/to/main/b3/directory/scripts/b3.sh'`. You can then, as an example,
  check the status of all your B3 instances by typing `b3 status` no matter the directory you are in.

_[www.bigbrotherbot.net](http://www.bigbrotherbot.net/) (2005-2011)_
