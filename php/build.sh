#!/bin/sh -xe

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}

BUILD_DIR=${DIR}/../build/snap/php

apt-get update && apt-get install -y \
		libfreetype6-dev \
		libjpeg62-turbo-dev \
		libpng-dev \
		libzip-dev \
		libsmbclient-dev \
		libxml2-dev \
		libsqlite3-dev \
		libpq-dev \
		libldap2-dev \
		libsasl2-dev \
		liblqr-1-0-dev \
		libfftw3-dev \
		libjbig-dev \
		libtiff5-dev \
		libwebp-dev \
		libmemcached-dev \
		libmcrypt-dev \
		zip \
		wget \
		unzip \
		libgmp-dev \
		libonig-dev \
		libicu-dev \
		libmagickwand-dev --no-install-recommends

mkdir -p /usr/src/php/ext/memcached
cd /usr/src/php/ext/memcached
wget https://github.com/php-memcached-dev/php-memcached/archive/v3.1.5.zip
unzip /usr/src/php/ext/memcached/v*.zip
mv /usr/src/php/ext/memcached/php-memcached-*/* /usr/src/php/ext/memcached/

docker-php-ext-configure memcached
docker-php-ext-install memcached
docker-php-ext-install gmp
pecl install imagick
pecl install smbclient
pecl install apcu
pecl install mcrypt-1.0.4
docker-php-ext-configure intl
docker-php-ext-install intl
docker-php-ext-enable apcu
docker-php-ext-install ldap
docker-php-ext-enable mcrypt
docker-php-ext-install bcmath
docker-php-ext-install pdo_mysql
docker-php-ext-install mysqli
docker-php-ext-install mbstring
docker-php-ext-install opcache
docker-php-ext-install zip
docker-php-ext-install pcntl
docker-php-ext-install exif
docker-php-ext-enable imagick
docker-php-ext-enable smbclient
docker-php-ext-install pdo pdo_pgsql
docker-php-ext-configure gd --with-freetype --with-jpeg
docker-php-ext-install -j2 gd
rm -rf /var/lib/apt/lists/*

php -i

rm -rf ${BUILD_DIR}
mkdir -p ${BUILD_DIR}
cp -r /etc ${BUILD_DIR}
cp -r /usr ${BUILD_DIR}
cp -r /bin ${BUILD_DIR}
cp -r /lib ${BUILD_DIR}

mv ${BUILD_DIR}/usr/lib/*-linux*/ImageMagick-*/modules-*/coders ${BUILD_DIR}/usr/lib/ImageMagickCoders
ls -la ${BUILD_DIR}/usr/lib/ImageMagickCoders
mkdir -p ${BUILD_DIR}/bin
cp ${DIR}/php.sh ${BUILD_DIR}/bin
cp ${DIR}/php-fpm.sh ${BUILD_DIR}/bin
mkdir -p ${BUILD_DIR}/lib/php/extensions
mv ${BUILD_DIR}/usr/local/lib/php/extensions/*/*.so ${BUILD_DIR}/lib/php/extensions
rm -rf ${BUILD_DIR}/usr/src
