# Usage
```stashcp [-d] [-r] [-h] -s <source> [-l <location to be copied to>]

	-d: show debugging information
	-r: recursively copy
	-h: show this help text
	
	--closest: return closest cache location

	Exit status 4 indicates that at least one file did not successfully copy over.
	Exit status 1 indicates that the WantsStashCache classad was not present.```


# Overview of algorithm 

All the functions are defined above everything else, so the code is not simple to read.  STASHCP itself starts "running" after the comment line `### LOGIC TO RUN STASHCP ###`.

###Startup
Before any downloading happens, STASHCP checks for relevant classads, loads xrootd, initializes information variables and processes arguments.  
#### Classads
In order to make sure that StashCache jobs are only sent to those sites that can handle them, users are required to add a StashCache classad to their jobs: `+WantsStashCache = true`  

If that classad is not present, STASHCP will stop, return 1, and print out an error message.
#### Information variables
The information variables are shell arrays holding strings corresponding to the start and end times of downloads, as well as the file or folder name and the size.  At the end of STASHCP, the information variables will be turned into strings and set as classads for the job.  Right now, because HTCondor limits classads to 1024 characters, the strings are truncated.

When a directory is downloaded, the information variables will be updated as if the directory were a single unit - the filename variable will hold just the directory path, the size will reflect the size of the directory, and the download times will reflect the downloading time for the directory.  This improves legibility and reduces space requirements.  If a user downloads a directory `mydir`, the information variable for filename will hold `mydir+`.  If a user downloads `mydir/`, the information variable for filename will hold `mydir/+`.
#### Argument processing


###Downloading
####Location Logic
**This is important to understand.**  
####Single file
This is where all the downloading actually happens.
####Directory

###Finishing
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