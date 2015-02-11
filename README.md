rdqdump is a simple utility to attempt to parse out json records
from a rabbit-mq cache file.

These .rdq files are usually in /var/lib/rabbitmq/mnesia/rabbit@servername/msg_store_persistent
and can sometimes be lost or corrupted when rabbit starts or crashes.

Usually the fix is to move them out of the path and attempt to move them individually
back into the path, restarting rabbit. 

Hopefully this offers another option of parsing out the records for reprocessing. The data
I recovered was json, if you have other data types, this may not work without some modification.
