rdqdump is a simple utility to attempt to parse out json records
from a rabbit-mq cache file.

These .rdq files are usually in /var/lib/rabbitmq/mnesia/rabbit@servername/msg_store_persistent
and can sometimes be lost or corrupted when rabbit starts or crashes.

Usually the fix is to move them out of the path and attempt to move them individually
back into the path, restarting rabbit. 

Hopefully this offers another option of parsing out the records for reprocessing. The data
I recovered was json, if you have other data types, this may not work without some modification.

Usage: 

`$ ./rdqdump.py --help`

Usage: rdqdump.py [options]

```
Options:
-h, --help   show this help message and exit
-b BYTES     number of bytes to show per line
-s START     starting byte
-l LENGTH    length in bytes to dump
-r CHUNK     length in bytes to read at a time
-f INPUT     input: filename
-x HEX       hex string to search for (395f316c000000016d0000 by default)
-c COUNT     count of hits to find before stopping (0 for don't stop)
-d, --debug  turn on debugging output
-z, --zero   when printing output, count from zero rather than position hit
             was found
```

sample run to print the first 2 records found: 

`$ ./rdqdump.py -f 383506.rdq -c2`

print all records:

`$ ./rdqdump.py -f 383506.rdq -c0`
