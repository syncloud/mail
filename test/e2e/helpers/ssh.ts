import { execFileSync } from 'node:child_process'
import { env } from './env'

const baseArgs = [
  '-o', 'StrictHostKeyChecking=no',
  '-o', 'UserKnownHostsFile=/dev/null',
  '-o', 'LogLevel=ERROR',
]

function target(): string {
  return `${env('PLAYWRIGHT_SSH_USER')}@${env('PLAYWRIGHT_DEVICE_HOST')}`
}

export function ssh(cmd: string, opts: { throw?: boolean } = {}): string {
  const args = ['-p', env('PLAYWRIGHT_SSH_PASSWORD'), 'ssh', ...baseArgs, target(), cmd]
  try {
    return execFileSync('sshpass', args, { encoding: 'utf8', timeout: 120_000 })
  } catch (e: any) {
    if (opts.throw === false) {
      return (e.stdout?.toString() ?? '') + (e.stderr?.toString() ?? '')
    }
    throw e
  }
}

export function scpFrom(remote: string, local: string, opts: { throw?: boolean } = {}): void {
  const args = ['-p', env('PLAYWRIGHT_SSH_PASSWORD'), 'scp', ...baseArgs, '-r', `${target()}:${remote}`, local]
  try {
    execFileSync('sshpass', args, { encoding: 'utf8', timeout: 120_000 })
  } catch (e) {
    if (opts.throw !== false) throw e
  }
}
