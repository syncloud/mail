local name = 'mail';
local roundcube = '1.6.1';
local python = '3.12-slim-bookworm';
local golang = '1.24.0';
local debian = 'bookworm-slim';
local bullseye = 'bullseye-slim';
local php_image = 'php:8.0.16-fpm-buster';
local postgres_image = 'postgres:9.4-alpine';
local platform = '26.04.10';
local playwright = 'mcr.microsoft.com/playwright:v1.48.2-jammy';
local deployer = 'https://github.com/syncloud/store/releases/download/4/syncloud-release';
local distro_default = 'bookworm';
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
      name: 'version',
      image: 'debian:' + debian,
      commands: [
        'echo $DRONE_BUILD_NUMBER > version',
      ],
    },
    {
      name: 'openssl',
      image: 'debian:' + debian,
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
  ] + std.flattenArrays([
    [
      {
        name: comp.name,
        image: comp.image,
        commands: [
          './' + comp.name + '/build.sh',
        ],
      },
    ] + [
      {
        name: comp.name + ' test ' + distro,
        image: platform_image(distro, arch),
        commands: [
          './' + comp.name + '/test.sh',
        ],
      }
      for distro in distros
    ]
    for comp in [
      { name: 'nginx', image: 'debian:' + debian },
      { name: 'dovecot', image: 'debian:' + debian },
      { name: 'opendkim', image: 'debian:' + bullseye },
      { name: 'php', image: php_image },
      { name: 'postgresql', image: postgres_image },
      { name: 'postfix', image: 'debian:' + debian },
    ]
  ]) + [
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
        'VERSION=$(cat version)',
        './package.sh ' + name + ' $VERSION ',
      ],
    },
  ] + [
    {
      name: 'test ' + distro,
      image: 'python:' + python,
      commands: [
        'APP_ARCHIVE_PATH=$(realpath $(cat package.name))',
        'cd integration',
        './deps.sh',
        'py.test -x -s verify.py --distro=' + distro + ' --domain=' + distro + '.com --app-archive-path=$APP_ARCHIVE_PATH --device-host=' + name + '.' + distro + '.com --app=' + name + ' --arch=' + arch,
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
           name: 'e2e-before-upgrade',
           image: playwright,
           commands: [
             './test/e2e/run.sh e2e-before-upgrade specs/02-pre-upgrade.spec.ts desktop',
           ],
         },
         {
           name: 'test-upgrade',
           image: 'python:' + python,
           commands: [
             'APP_ARCHIVE_PATH=$(realpath $(cat package.name))',
             'cd integration',
             './deps.sh',
             'py.test -x -s test-upgrade.py --distro=' + distro_default + ' --domain=' + distro_default + '.com --app-archive-path=$APP_ARCHIVE_PATH --device-host=' + name + '.' + distro_default + '.com --app=' + name + ' --arch=' + arch,
           ],
         },
         {
           name: 'e2e-after-upgrade',
           image: playwright,
           commands: [
             './test/e2e/run.sh e2e-after-upgrade specs/03-post-upgrade.spec.ts desktop',
           ],
         },
       ] else []) + [
    {
      name: 'upload',
      image: 'debian:' + debian,
      environment: {
        AWS_ACCESS_KEY_ID: { from_secret: 'AWS_ACCESS_KEY_ID' },
        AWS_SECRET_ACCESS_KEY: { from_secret: 'AWS_SECRET_ACCESS_KEY' },
        SYNCLOUD_TOKEN: { from_secret: 'SYNCLOUD_TOKEN' },
      },
      commands: [
        'PACKAGE=$(cat package.name)',
        'apt update && apt install -y wget',
        'wget ' + deployer + '-' + arch + ' -O release --progress=dot:giga',
        'chmod +x release',
        './release publish -f $PACKAGE -b $DRONE_BRANCH',
      ],
      when: {
        branch: ['stable', 'master'],
        event: ['push'],
      },
    },
    {
      name: 'promote',
      image: 'debian:' + debian,
      environment: {
        AWS_ACCESS_KEY_ID: { from_secret: 'AWS_ACCESS_KEY_ID' },
        AWS_SECRET_ACCESS_KEY: { from_secret: 'AWS_SECRET_ACCESS_KEY' },
        SYNCLOUD_TOKEN: { from_secret: 'SYNCLOUD_TOKEN' },
      },
      commands: [
        'apt update && apt install -y wget',
        'wget ' + deployer + '-' + arch + ' -O release --progress=dot:giga',
        'chmod +x release',
        './release promote -n ' + name + ' -a $(dpkg --print-architecture)',
      ],
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
        source: ['artifact/*'],
        strip_components: 1,
      },
      when: {
        status: ['failure', 'success'],
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
