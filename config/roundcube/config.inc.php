<?php

$config = array();

$config['log_dir'] = '/opt/data/mail/log/';

$config['db_dsnw'] = 'pgsql://mail:@unix(/opt/data/mail/postgresql)/mail';

$config['default_host'] = 'localhost';

$config['support_url'] = '';
$config['des_key'] = '46adfbf655e235b60f56f881';

$config['smtp_server'] = 'localhost';
$config['smtp_user'] = '%u';
$config['smtp_pass'] = '%p';

$config['plugins'] = array();

$config['default_host'] = 'tls://localhost';

$config['imap_conn_options'] = array(
  'ssl' => array(
      'verify_peer' => true,
      'allow_self_signed' => true,
      'verify_depth' => 3,
       'ciphers' => 'TLSv1+HIGH:!aNull:@STRENGTH',
       'cafile' => '/opt/data/platform/syncloud.ca.crt', ), 
    );
