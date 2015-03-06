BigBrotherBot (B3) management script
====================================

### What is this?

In this directory you can find a bash script file, `b3.sh`, which can be used to manage B3 instances on Linux systems. 
The script provides a set of tools that will allow you to:

* Launch multiple B3 instances (as background processes) using a single B3 installation
* Shutdown gracefully alive B3 instances
* Monitor the status of your B3 instances (and list the available ones)
* Clean B3 directory from Python compiled sources (in case you need a fresh compile of a python module)
* Check for the Python interpreter to be installed in your system
* Check that you have installed the correct Python version to run B3 (version **2.7**)
* Prevent from running B3 instances as super user: **root**

### Requirements

* Linux system (tested on Debian, Ubuntu)
* Bash shell
* [Screen](http://linux.die.net/man/1/screen) window manager

In order for B3 to work correctly using this script you need to setup a Linux system user that will run B3. Such user
will have to be proprietory of all the B3 files. If for example your system user is **b3** and belongs to the group **users** 
you can then change ownership of all the B3 files to belong to the **b3** user by typing the following in the Linux console: 
`chown -R b3:users /path/to/main/b3/directory`. For information on how to add a Linux system user, please refer to
the [man page](http://linux.die.net/man/8/useradd)

### How to use

As described above, the script will allow you to launch multiple B3 instances so you can manage multiple game servers.
In order to do that you need to specify multiple B3 configuration files to be used to start B3 instances: those 
configuration files needs to be placed in the B3 main configuration directory (namely **b3/conf**). The names of such
configuration files needs to follow a specific pattern: `b3_[<name>].[.ini|.xml]` (*.ini* format will be introduced soon 
as B3 main configuration file, but this script is already .ini capable).  

As an example let's assume you are running 2 game servers and you need to start **2** B3 intances: let's call them 
**tdm** and **ctf**. What you need to do is pretty simple: you need to create **2** configuration files and place them 
in the B3 main configuration directory as follows:

* **tdm**: create a `b3_tdm.xml` file in `b3/conf/b3_tdm.xml`
* **ctf**: create a `b3_ctf.xml` file in `b3/conf/b3_ctf.xml`

*NOTE: you can obviously customize those configuration files as you want and thus you can load different plugins and 
different plugin configuration files on every B3 instance you intend to run.*

After saving such configuration files, you are ready to launch your B3 instances using the `b3.sh` script:  the script 
autodiscovers new configuration files and let you interact with them by using the chosen B3 instance name as input parameter.
So, in the example above you can launch the **tdm** and **ctf** B3 instanced by typing:

* `./b3.sh start tdm`
* `./b3.sh start ctf`

The script will inform you on the result of the startup operation: you can then check the status of the B3 processes
using the `status` command provided by the `b3.sh` script.  
Note that the B3 instance `<name>` parameter is optional: if you do not specify it the script will execute the given 
operation on all the B3 instances it can find (so in the previous example you could have just typed `./b3.sh start` to 
start both the **tdm** and **ctf** B3 instances.

### Commands reference

```bash
-usage: b3.sh 
               start   [<name>] - start B3
               stop    [<name>] - stop B3
               restart [<name>] - restart B3
               status  [<name>] - display current B3 status
               clean            - clean B3 directory
```

### For advanced users

* You can enable logging by setting the `LOG_ENABLED` variable to `1`: log will be available in `b3/scripts/log/b3_init.log`
  and will contain the console output produced by this very script
* You can turn off bash colors setting the `USE_COLORS` variable to `0`: while the usage is adviced for a fast reading
  and understanding of the console output, some people may not like them and thus I left in the possibility to turn them off
* If you want to be able to control all your B3 instances no matter the current working directory you can setup an alias
  in your user `.bash_profile` file: `alias b3='/path/to/main/b3/directory/scripts/b3.sh'`. You can then, as an example,
  check the status of all your B3 instances by typing `b3 status` no matter the directory you are in

_[www.bigbrotherbot.net](http://www.bigbrotherbot.net/) (2005-2011)_
