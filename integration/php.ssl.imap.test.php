<?php

require('/config.inc.php');
$stream_context = stream_context_create($config['imap_conn_options']);

$fp = stream_socket_client($config['default_host'],
   $errno, $errstr, 30, STREAM_CLIENT_CONNECT, $stream_context);
fwrite($fp, "A Logout\n");
while($line = fgets($fp, 8192)) echo $line;