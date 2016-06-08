import pyuarm

def main():
    for p in pyuarm.list_uarms():
        print (p)
    print ("{0} ports found".format(len(pyuarm.list_uarms())))

if __name__ == '__main__':
    main()
