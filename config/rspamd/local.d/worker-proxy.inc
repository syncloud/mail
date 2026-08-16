bind_socket = "{{ .DataDir }}/rspamd/milter.sock mode=0666";
milter = yes;
timeout = 120s;
upstream "local" {
  default = yes;
  self_scan = yes;
}
