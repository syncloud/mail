<?php

require('/config.inc.php');
$stream_context = stream_context_create($config['imap_conn_options']);

$socket = stream_socket_client($config['default_host'] . ':143',
   $errno, $errstr, 30, STREAM_CLIENT_CONNECT, $stream_context);
if ($socket) {
    fwrite($socket, "A Logout\n");
    while($line = fgets($socket, 8192))
        echo $line;
} else {
    echo "Failure $errno errstr $errstr.\n";
}

