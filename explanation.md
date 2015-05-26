# Overview of algorithm 

All the functions are defined above everything else, so the code is not simple to read.  STASHCP itself starts "running" after the comment line "### LOGIC TO RUN STASHCP ###".

###Startup
Before any downloading happens, STASHCP checks for relevant classads, loads xrootd, initializes information variables and processes arguments.  
##### Classads
In order to make sure that StashCache jobs are only sent to those sites that can handle them, users are required to add a StashCache classad to their jobs: `+WantsStashCache = true`
##### Information variables
The information variables are shell arrays holding strings corresponding to the start and end times of downloads, as well as the file or folder name and the size.  At the end of STASHCP, the information variables will be turned into strings and set as classads for the job.  
##### Argument processing

# Known issues and concerns 

* Relies on geoip to find closest cache
  - Geoip doesn't always work
  - Closest cache isn't necessarily the best cache
  - No checking for "next-closest" cache if closest cache is temporarily down and status is not yet reflected in caches.json
	
* Call could be simpler, without requiring the use of flags for every argument
  - Want: stashcp <FILE> <LOCATION> <FLAGS>
  - Have: stashcp -s <FILE> -l <LOCATION> <FLAGS>
	
* Static hard-coded number of attempts to pull from cache (2) and trunk (1)
  - Does not take type of error/failure into account
  - If the closest cache is the trunk, then the algorithm will attempt to pull from the trunk 3 times, instead of 1 or 2
	
* Relies explicitly on the trunk being up in order to run critical steps
  - In particular, relies on trunk being up in order to get size of file or to get contents of directory
  - Could lead to unnecessary failure when the trunk is down but files are already present and accounted for on closest cache
	
* Does not do anything else if stashcp fails
  - Maybe if stashcp from the local cache and from the trunk fail, should try wget?  Hard to think of a situation when wget would work but stashcp from the trunk would not.
	
* Error messages are not informative for users
  - Messages written for the coder to use