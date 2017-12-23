<?php

$config = array();
$config['imap_debug'] = true;
$config['ldap_debug'] = true;
$config['smtp_debug'] = true;
$config['log_dir'] = '{{ app_data_dir }}/log/';

$config['db_dsnw'] = 'pgsql://mail:@unix({{ db_psql_path }}:{{ db_psql_port }})/{{ db_name }}';

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
       'cafile' => '{{ platform_data_dir }}/syncloud.ca.crt',
       'capath' => '/etc/ssl/certs',
       ),
    );
