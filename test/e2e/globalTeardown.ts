import { ssh, scpFrom } from './helpers/ssh'
import { env } from './helpers/env'
import * as path from 'node:path'
import * as fs from 'node:fs'

const TMP_DIR = '/tmp/syncloud/mail-ui'

export default async function () {
  const out = path.join(env('PLAYWRIGHT_ARTIFACT_DIR'), 'logs', env('PLAYWRIGHT_PROJECT'))
  fs.mkdirSync(out, { recursive: true })
  ssh(`mkdir -p ${TMP_DIR}`, { throw: false })
  ssh(`journalctl -u snap.mail.bulwark > ${TMP_DIR}/bulwark.log`, { throw: false })
  ssh(`journalctl -u snap.mail.stalwart > ${TMP_DIR}/stalwart.log`, { throw: false })
  scpFrom(`${TMP_DIR}/*`, out, { throw: false })
}
