<?php

$config = array();

$config['log_dir'] = '{{ app_data_dir }}/log/';

$config['db_dsnw'] = 'pgsql://mail:@unix({{ db_psql_path }}:{{ db_psql_port }})/{{ db_name }}';

$config['support_url'] = '';
$config['des_key'] = '46adfbf655e235b60f56f881';

$config['smtp_server'] = 'localhost';
$config['smtp_user'] = '%u';
$config['smtp_pass'] = '%p';

$config['plugins'] = array();
$config['mail_domain'] = '{{ device_domain_name }}';
$config['default_host'] = 'tls://localhost';

$config['imap_conn_options'] = array(
  'ssl' => array(
      'verify_peer' => true,
      'peer_name' => '{{ device_domain_name }}',
      'allow_self_signed' => true,
      'verify_depth' => 3,
      'ciphers' => 'TLSv1+HIGH:!aNull:@STRENGTH:!SSLv2:!SSLv3',
      'cafile' => '{{ platform_data_dir }}/syncloud.ca.crt',
      'capath' => '/etc/ssl/certs',
     ),
  );
