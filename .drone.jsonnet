local name = 'mail';
local roundcube = '1.6.1';
local dovecot = '2.3.16';
local nginx = '1.24.0';
local postfix = '3.4.28';
local python = '3.12-slim-bookworm';
local golang = '1.24.0';
local debian = 'bookworm-slim';
local bullseye = 'bullseye-slim';
local buster = 'buster-slim';
local php = 'php:8.0.16-fpm-buster';
local postgres = 'postgres:9.4-alpine';
local platform = '26.04.10';
local playwright = 'mcr.microsoft.com/playwright:v1.48.2-jammy';
local store_publisher = 'stable-303';
local distros = ['bookworm', 'buster'];

local platform_image(distro, arch) =
  'syncloud/platform-' + distro + '-' + arch + ':' + platform;

local build(arch, test_ui) = [{
  kind: 'pipeline',
  type: 'docker',
  name: arch,
  platform: {
    os: 'linux',
    arch: arch,
  },
  steps: [
    {
      name: 'openssl',
      image: 'debian:' + buster,
      commands: [
        './openssl/build.sh',
      ],
    },
    {
      name: 'openssl test',
      image: 'debian:' + debian,
      commands: [
        './openssl/test.sh',
      ],
    },
    {
      name: 'nginx',
      image: 'nginx:' + nginx,
      commands: [
        './nginx/build.sh',
      ],
    },
  ] + [
    {
      name: 'nginx test ' + distro,
      image: platform_image(distro, arch),
      commands: [
        './nginx/test.sh',
      ],
    }
    for distro in distros
  ] + [
    {
      name: 'dovecot',
      image: 'debian:' + debian,
      commands: [
        './dovecot/build.sh ' + dovecot,
      ],
    },
  ] + [
    {
      name: 'dovecot test ' + distro,
      image: platform_image(distro, arch),
      commands: [
        './dovecot/test.sh',
      ],
    }
    for distro in distros
  ] + [
    {
      name: 'opendkim',
      image: 'debian:' + bullseye,
      commands: [
        './opendkim/build.sh',
      ],
    },
  ] + [
    {
      name: 'opendkim test ' + distro,
      image: platform_image(distro, arch),
      commands: [
        './opendkim/test.sh',
      ],
    }
    for distro in distros
  ] + [
    {
      name: 'php',
      image: php,
      commands: [
        './php/build.sh',
      ],
    },
  ] + [
    {
      name: 'php test ' + distro,
      image: platform_image(distro, arch),
      commands: [
        './php/test.sh',
      ],
    }
    for distro in distros
  ] + [
    {
      name: 'postgresql',
      image: postgres,
      commands: [
        './postgresql/build.sh',
      ],
    },
  ] + [
    {
      name: 'postgresql test ' + distro,
      image: platform_image(distro, arch),
      commands: [
        './postgresql/test.sh',
      ],
    }
    for distro in distros
  ] + [
    {
      name: 'postfix',
      image: 'debian:' + debian,
      commands: [
        './postfix/build.sh ' + postfix,
      ],
    },
  ] + [
    {
      name: 'postfix test ' + distro,
      image: platform_image(distro, arch),
      commands: [
        './postfix/test.sh',
      ],
    }
    for distro in distros
  ] + [
    {
      name: 'download',
      image: 'debian:' + debian,
      commands: [
        './download.sh ' + roundcube,
      ],
    },
    {
      name: 'cli',
      image: 'golang:' + golang,
      commands: [
        './cli/build.sh',
      ],
    },
    {
      name: 'package',
      image: 'debian:' + debian,
      commands: [
        './package.sh ' + name + ' $DRONE_BUILD_NUMBER',
      ],
    },
  ] + [
    {
      name: 'test ' + distro,
      image: 'python:' + python,
      commands: [
        './test/ci-test.sh ' + distro + ' ' + arch,
      ],
    }
    for distro in distros
  ] + (if test_ui then [
         {
           name: 'e2e',
           image: playwright,
           commands: [
             './test/e2e/run.sh e2e specs/01-smoke.spec.ts desktop',
           ],
         },
         {
           name: 'e2e-mobile',
           image: playwright,
           commands: [
             './test/e2e/run.sh e2e specs/01-smoke.spec.ts mobile',
           ],
         },
         {
           name: 'test-upgrade',
           image: 'python:' + python,
           commands: [
             './test/ci-upgrade.sh buster ' + arch,
           ],
         },
       ] else []) + [
    {
      name: 'publish',
      image: 'syncloud/store-publisher:' + store_publisher,
      environment: {
        SYNCLOUD_TOKEN: { from_secret: 'SYNCLOUD_TOKEN' },
      },
      command: ['snap', '-c', '${DRONE_BRANCH}'],
      when: {
        branch: ['master', 'stable'],
        event: ['push'],
      },
    },
    {
      name: 'artifact',
      image: 'appleboy/drone-scp:1.6.4',
      settings: {
        host: { from_secret: 'artifact_host' },
        username: 'artifact',
        key: { from_secret: 'artifact_key' },
        timeout: '2m',
        command_timeout: '2m',
        target: '/home/artifact/repo/' + name + '/${DRONE_BUILD_NUMBER}-' + arch,
        source: 'artifact/*',
        strip_components: 1,
      },
      when: {
        status: ['failure', 'success'],
        event: ['push'],
      },
    },
  ],
  trigger: {
    event: ['push'],
  },
  services: [
    {
      name: name + '.' + distro + '.com',
      image: platform_image(distro, arch),
      privileged: true,
      volumes: [
        { name: 'dbus', path: '/var/run/dbus' },
        { name: 'dev', path: '/dev' },
      ],
    }
    for distro in distros
  ],
  volumes: [
    { name: 'dbus', host: { path: '/var/run/dbus' } },
    { name: 'dev', host: { path: '/dev' } },
  ],
}];

build('amd64', true) +
build('arm64', false) +
build('arm', false)
