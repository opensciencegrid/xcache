import getopt, sys, subprocess

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:l:o:")
    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)
    fileString = ''
    loc = ''
    outfile = ''
    for opt, arg in opts:
        if opt == "-f":
            fileString = arg
        elif opt == "-l":
            loc = arg
        elif opt == "-o":
            outfile = arg
    files = fileString.split(",")
    subprocess.Popen("source /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/5.6.2/init/bash")
    subprocess.Popen("module load xrootd/4.1.1 2>&1")
    subprocess.Popen("source ./setStashCache.sh")
    for f in files:
        subprocess.Popen("bash ./stashcp -d -s {!s} -l {!s} > {!s}".format(f, loc, outfile))
    
if __name__ == "__main__":
    main()
