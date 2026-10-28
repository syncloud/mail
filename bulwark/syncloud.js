const fs = require('fs')
const http = require('http')
const net = require('net')
const path = require('path')
const { Agent, buildConnector, setGlobalDispatcher } = require(path.join(__dirname, 'node_modules', 'undici'))

const listenSocket = process.env.BULWARK_SOCKET
const jmapHost = process.env.BULWARK_JMAP_HOST
const jmapSocket = process.env.BULWARK_JMAP_SOCKET

if (listenSocket) {
  const listen = http.Server.prototype.listen
  http.Server.prototype.listen = function () {
    fs.rmSync(listenSocket, { force: true })
    this.once('listening', () => fs.chmodSync(listenSocket, 0o660))
    return listen.call(this, listenSocket)
  }
}

if (jmapHost && jmapSocket) {
  const connect = buildConnector({})
  setGlobalDispatcher(new Agent({
    connect (options, callback) {
      if (options.hostname !== jmapHost) {
        return connect(options, callback)
      }
      const socket = net.connect(jmapSocket)
      socket.once('connect', () => callback(null, socket))
      socket.once('error', (error) => callback(error, null))
    }
  }))
}
