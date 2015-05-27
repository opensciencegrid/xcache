# Usage
```
stashcp [-d] [-r] [-h] -s <source> [-l <location to be copied to>]

-d: show debugging information
-r: recursively copy
-h: show this help text
	
--closest: return closest cache location

Exit status 4 indicates that at least one file did not successfully copy over.
Exit status 1 indicates that the WantsStashCache classad was not present.
```

# Overview of algorithm 

All the functions are defined above everything else, so the code is not simple to read.  STASHCP itself starts "running" after the comment line `### LOGIC TO RUN STASHCP ###`.

### Startup
Before any downloading happens, STASHCP checks for relevant classads, loads xrootd, initializes information variables and processes arguments.  It also determines the closest local cache.

#### Classads
In order to make sure that StashCache jobs are only sent to those sites that can handle them, users are required to add a StashCache classad to their jobs: `+WantsStashCache = true`  

If that classad is not present, STASHCP will stop, return 1, and print out an error message.

#### Information variables
The information variables are shell arrays holding strings corresponding to the start and end times of downloads, as well as the file or folder name and the size.  At the end of STASHCP, the information variables will be turned into strings and set as classads for the job.  Right now, because HTCondor limits classads to 1024 characters, the strings are truncated.

When a directory is downloaded, the information variables will be updated as if the directory were a single unit - the filename variable will hold just the directory path, the size will reflect the size of the directory, and the download times will reflect the downloading time for the directory.  This improves legibility and reduces space requirements.  If a user downloads a directory `mydir`, the information variable for filename will hold `mydir+`.  If a user downloads `mydir/`, the information variable for filename will hold `mydir/+`.

#### Arguments
STASHCP only requires a single argument, the source.  Every other argument is optional.
* `-s <source>` : `<source>` is the *comma-delimited* list of files and/or directories that the user wishes to download.  The path of a given file will be of the form `user/<username>/public/<path in STASH>`.  
* `-l <location>` : `<location>` is the location within the job directory that the user wishes to download their files/directories to.  This can only be a single location.  If the directory does not exist when STASHCP is run, STASHCP will fail and return 1.
* `-d` : if this flag is present, print debugging information.
* `-r` : if this flag is present, download recursively (all subfolders).

#### Local cache
Simply calls `setStashCache.sh` and holds the result.  The called code uses geoip information and the `caches.json` file to determine to closest active cache.

### Main Loop
This loop iterates over every file/directory that the user wishes to download. 

Before any downloading occurs, STASHCP checks to see if the source currently being examined is a file or a directory.  

#### Location Logic
**This is important to understand.  Check back later for the actual information.**  

Due to numerous problems with trying to do this recursively, I decided to take a more direct approach and have STASHCP use the full source file path to direct location logic.  



#### doStashCpSingle
This is where all the downloading actually happens.  

This function can take two arguments.  The first one, which is required, is the name of the file to be downloaded.  If the second argument is present, the function will update the information variables with information about this particular file download.  If the second argument is not present, no updating of information variables occurs (such as when the file being downloaded is but one member of a larger directory being downloaded).  

`doStashCpSingle` first determines the size of the file, and from that calculates a timeout period (5m + 1s/MB).  Since the built-in timeout utility isn't present on all OSG sites, a standalone version is included.  

`doStashCpSingle` attempts to run `xrdcp` from the local cache, keeping track of start and end time.  If this pull is not successful, a second `xrdcp` from local is attempted.  Should that pull fail, STASHCP fails over to pulling from the trunk, and failover information is updated.  The last pull, directly from the trunk, is given a 10x longer timeout period.  If no pull is successful, failure information is updated.  However, if any pull is successful, the usual information variables are updated.

#### doStashCpDirectory
Like [doStashCpSingle](#dostashcpsingle), this function can take two arguments - the first is the directory to be downloaded, and the second is a flag to let the function know if it should update information.  Information should not be updated if the directory being currently downloaded is a subdirectory of a larger directory being downloaded.

`doStashCpDirectory` iterates through the contents of the input directory.  If an item is a file, `doStashCpSingle` is called on the item.  If the item is a directory, and the recursive flag `-r` has been set, then the appropriate directory is created and `doStashCpDirectory` is called on the item recursively.   The time it takes to iterate and download all of the contents is recorded and, if appropriate, updated to the information variables.

### Finishing
The information variables are chirped, as described [above](#information-variables).

If any single download failed, STASHCP itself has failed.  In this case, STASHCP returns 4.

# Known issues and concerns 

* Relies on geoip to find closest cache
  - Geoip doesn't always work
  - Closest cache isn't necessarily the best cache
  - No checking for "next-closest" cache if closest cache is temporarily down and status is not yet reflected in caches.json
	
* Call could be simpler, without requiring the use of flags for every argument
  - Want: `stashcp <FILE> <LOCATION> <FLAGS>`
  - Have: `stashcp -s <FILE> -l <LOCATION> <FLAGS>`
	
* Static hard-coded number of attempts to pull from cache (2) and trunk (1)
  - Does not take type of error/failure into account
  - If the closest cache is the trunk, then the algorithm will attempt to pull from the trunk 3 times, instead of 1 or 2
	
* Relies explicitly on the trunk being up in order to run critical steps
  - In particular, relies on trunk being up in order to get size of file or to get contents of directory
  - Could lead to unnecessary failure when the trunk is down but files are already present and accounted for on closest cache
	
* Does not do anything else if stashcp fails
  - Maybe if stashcp from the local cache and from the trunk fail, should try wget?  Hard to think of a situation when wget would work but stashcp from the trunk would not.
	
* Error messages are not informative for users
  - Messages written only for the coder to use