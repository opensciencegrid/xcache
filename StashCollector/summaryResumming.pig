rmf Resummed;

REGISTER '/home/ivukotic/piggybank-0.14.0.jar' ;

REGISTER '/usr/lib/pig/lib/avro-*.jar';
REGISTER '/usr/lib/pig/lib/jackson-*.jar';
REGISTER '/usr/lib/pig/lib/json-*.jar';
REGISTER '/usr/lib/pig/lib/jython-*.jar';
REGISTER '/usr/lib/pig/lib/snappy-*.jar';

--REGISTER 'cleanup.py' using jython as cleanfuncs;

RAW = LOAD '/user/ivukotic/Cleaned' as (SRC:chararray,SITE:chararray,TOS:long,TOD:long,TOE:long,IN:long,OUT:long); 

--RAWL = LIMIT RAW 1000;
--dump RAWL;

cleaned = foreach RAW generate FLATTEN(cleanfuncs.XMLtoNTUP(x));
--dump cleaned;
STORE cleaned into 'Cleaned';