import getopt, sys

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:l:")
    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)
    fileString = ''
    loc = ''
    for opt, arg in opts:
        if opt == "-f":
            fileString = arg
        elif opt == "-l"
            loc = arg
    files = fileString.split(",")
    print files
    
if __name__ == "__main__":
    main()