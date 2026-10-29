local name = 'mail';
local stalwart = 'v1.0.1-syncloud.1';
local webui = 'v2.0.1';
local spam_filter = 'v3.0.3';
local bulwark = '1.18.0';
local node = 'node:22.23.4-bookworm-slim';
local nginx = '1.30.4';
local python = '3.12-slim-bookworm';
local golang = '1.24.0';
local debian = 'bookworm-slim';
local platform = '26.10.02';
local playwright = 'mcr.microsoft.com/playwright:v1.48.2-jammy';
local store_publisher = 'stable-346';
local distros = ['bookworm', 'buster'];
local distro_default = 'bookworm';

local platform_image(distro) =
  'syncloud/platform-' + distro + ':' + platform;

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
      name: 'nginx',
      image: 'nginx:' + nginx,
      commands: [
        './nginx/build.sh',
      ],
    },
  ] + [
    {
      name: 'nginx test ' + distro,
      image: platform_image(distro),
      commands: [
        './nginx/test.sh',
      ],
    }
    for distro in distros
  ] + [
    {
      name: 'stalwart',
      image: 'debian:' + debian,
      commands: [
        './stalwart/build.sh ' + stalwart + ' ' + webui + ' ' + spam_filter,
      ],
    },
  ] + [
    {
      name: 'stalwart test ' + distro,
      image: platform_image(distro),
      commands: [
        './stalwart/test.sh',
      ],
    }
    for distro in distros
  ] + [
    {
      name: 'bulwark',
      image: node,
      commands: [
        './bulwark/build.sh ' + bulwark,
      ],
    },
  ] + [
    {
      name: 'bulwark test ' + distro,
      image: platform_image(distro),
      commands: [
        './bulwark/test.sh',
      ],
    }
    for distro in distros
  ] + [
    {
      name: 'cli',
      image: 'golang:' + golang,
      commands: [
        './cli/build.sh',
      ],
    },
    {
      name: 'redirect faker',
      image: 'golang:' + golang,
      commands: [
        './redirect-faker/build.sh',
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
      name: 'redirect.' + distro + '.com',
      image: 'debian:' + debian,
      detach: true,
      commands: [
        './redirect-faker/faker',
      ],
    }
    for distro in distros
  ] + [
    {
      name: 'mail-relay.' + distro + '.com',
      image: 'debian:' + debian,
      detach: true,
      commands: [
        './redirect-faker/faker',
      ],
    }
    for distro in distros
  ] + [
    {
      name: 'test ' + distro,
      image: 'python:' + python,
      commands: [
        './ci/test.sh test.py ' + distro + ' ' + arch,
      ],
    }
    for distro in distros
  ] + (if test_ui then [
         {
           name: 'e2e',
           image: playwright,
           commands: [
             './test/e2e/run.sh specs/01- desktop',
           ],
         },
         {
           name: 'e2e-mobile',
           image: playwright,
           commands: [
             './test/e2e/run.sh specs/01-smoke.spec.ts mobile',
           ],
         },
         {
           name: 'test-migrate-postfix-before',
           image: 'python:' + python,
           commands: [
             './ci/test.sh migrate_postfix_before.py ' + distro_default + ' ' + arch,
           ],
         },
         {
           name: 'e2e-migrate-postfix-before',
           image: playwright,
           commands: [
             './test/e2e/run.sh specs/02-migrate-postfix-before.spec.ts desktop',
           ],
         },
         {
           name: 'test-migrate-postfix',
           image: 'python:' + python,
           commands: [
             './ci/test.sh migrate_postfix.py ' + distro_default + ' ' + arch,
           ],
         },
         {
           name: 'e2e-migrate-postfix-after',
           image: playwright,
           commands: [
             './test/e2e/run.sh specs/03-migrate-postfix-after.spec.ts desktop',
           ],
         },
         {
           name: 'e2e-migrate-postfix-after-mobile',
           image: playwright,
           commands: [
             './test/e2e/run.sh specs/03-migrate-postfix-after.spec.ts mobile',
           ],
         },
       ] else []) + [
    {
      name: 'test-upgrade',
      image: 'python:' + python,
      commands: [
        './ci/test.sh upgrade.py ' + distro_default + ' ' + arch,
      ],
    },
    {
      name: 'publish',
      image: 'syncloud/store-publisher:' + store_publisher,
      environment: {
        SYNCLOUD_TOKEN: { from_secret: 'SYNCLOUD_TOKEN' },
      },
      command: ['snap', '-c', '${DRONE_BRANCH}'],
      when: {
        branch: ['stable'],
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
      image: platform_image(distro),
      privileged: true,
      entrypoint: ['/bin/sh', '-c', "mkdir -p /etc/systemd/system/snapd.service.d && printf '[Service]\\nExecStartPost=/bin/sh -c \"/usr/bin/snap set system refresh.hold=2099-01-01T00:00:00Z\"\\n' > /etc/systemd/system/snapd.service.d/disable-refresh.conf && exec /sbin/init"],
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
