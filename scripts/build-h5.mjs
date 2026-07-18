import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const uniCli = path.join(
  projectRoot,
  'node_modules',
  '@dcloudio',
  'vite-plugin-uni',
  'bin',
  'uni.js'
)

const result = spawnSync(process.execPath, [uniCli, 'build', '-p', 'h5'], {
  cwd: projectRoot,
  env: {
    ...process.env,
    UNI_INPUT_DIR: projectRoot,
    UNI_OUTPUT_DIR: path.join(projectRoot, 'dist', 'build', 'h5')
  },
  stdio: 'inherit'
})

if (result.error) {
  throw result.error
}

process.exit(result.status ?? 1)
