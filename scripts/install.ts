/**
 * Install built skills into a destination project.
 *
 * Migrated from `scripts/install.py`. Uses only Node built-ins — zero npm dependencies.
 *
 * Run with one of:
 *   bun scripts/install.ts ...
 *   node --experimental-strip-types scripts/install.ts ...    (Node 22+)
 *   npx tsx scripts/install.ts ...                            (after `npm i -g tsx`)
 *
 * Usage:
 *   install.ts                                       (interactive wizard — no args)
 *   install.ts -i                                    (force wizard with other args)
 *   install.ts -t claude -d ~/my-project
 *   install.ts -t claude -d ~/my-project -s database-access
 *   install.ts -t claude -d ~/my-project --dry-run
 *   install.ts -t claude -d ~/my-project --force
 */

import { parseArgs } from 'node:util';
import { access, copyFile, mkdir, readdir, stat } from 'node:fs/promises';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';
import { createInterface } from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';

// ─── Constants ──────────────────────────────────────────────────────────

const TARGETS = ['claude', 'opencode', 'roo', 'codex'] as const;
type Target = (typeof TARGETS)[number];

const TARGET_DESCRIPTIONS: Record<Target, string> = {
  claude:   'Claude Code (.claude/skills/<slug>/)',
  opencode: 'OpenCode (.opencode/skills/<slug>/)',
  roo:      'Roo Code (.roo/rules/<NN>-<slug>.md)',
  codex:    'OpenAI Codex CLI (single AGENTS.md, all skills concatenated)',
};

// Resolve repo root from this file's location: scripts/install.ts → ../
const __filename = fileURLToPath(import.meta.url);
const __dirname  = dirname(__filename);
const REPO_ROOT  = resolve(__dirname, '..');
const DIST_DIR   = join(REPO_ROOT, 'dist');

// ─── Small utilities ────────────────────────────────────────────────────

function expandHome(p: string): string {
  return p.startsWith('~') ? join(homedir(), p.slice(1)) : p;
}

async function exists(p: string): Promise<boolean> {
  try { await access(p); return true; } catch { return false; }
}

async function isDirectory(p: string): Promise<boolean> {
  try { return (await stat(p)).isDirectory(); } catch { return false; }
}

// Color helpers — no-op when stdout isn't a TTY (so piped output stays clean).
function color(code: string, text: string): string {
  return process.stdout.isTTY ? `\x1b[${code}m${text}\x1b[0m` : text;
}
const bold   = (s: string) => color('1',  s);
const dim    = (s: string) => color('2',  s);
const cyan   = (s: string) => color('36', s);
const green  = (s: string) => color('32', s);
const yellow = (s: string) => color('33', s);
const red    = (s: string) => color('31', s);

// ─── Walking dist/<target>/ ─────────────────────────────────────────────

/**
 * Walk a target's dist directory and return [absoluteSrcPath, relativeDestPath] tuples.
 * If `skill` is provided, filter to files belonging to that skill (matching either by
 * path component or by filename containing the slug — same rules as the Python version).
 */
async function iterInstallFiles(
  srcRoot: string,
  skill: string | null,
): Promise<Array<[src: string, rel: string]>> {
  if (!(await isDirectory(srcRoot))) {
    const targetName = relative(DIST_DIR, srcRoot);
    throw new Error(
      `${srcRoot} does not exist — run \`python -m scripts.build --target ${targetName}\` first`,
    );
  }

  const entries = await readdir(srcRoot, { recursive: true, withFileTypes: true });
  const pairs: Array<[string, string]> = [];

  for (const entry of entries) {
    if (!entry.isFile()) continue;
    // `parentPath` is Node ≥ 20.12; older Node uses `path`. Support both.
    const parentPath = (entry as { parentPath?: string; path?: string }).parentPath
                    ?? (entry as { parentPath?: string; path?: string }).path
                    ?? srcRoot;
    const absSrc = join(parentPath, entry.name);
    const rel    = relative(srcRoot, absSrc);

    if (skill !== null) {
      const inPath = rel.split(/[/\\]/).includes(skill);
      const inName = entry.name.includes(skill);
      if (!inPath && !inName) continue;
    }

    pairs.push([absSrc, rel]);
  }

  return pairs;
}

/**
 * Walk dist/<target>/ and extract distinct skill slugs from paths and filenames.
 * Used by the interactive wizard to populate the skill picker.
 */
async function discoverSkills(target: Target): Promise<string[]> {
  if (target === 'codex') {
    // Codex output is always a single AGENTS.md containing all skills.
    return [];
  }

  const srcRoot = join(DIST_DIR, target);
  if (!(await isDirectory(srcRoot))) return [];

  const slugs = new Set<string>();
  const entries = await readdir(srcRoot, { recursive: true, withFileTypes: true });

  for (const entry of entries) {
    if (!entry.isFile()) continue;
    const parentPath = (entry as { parentPath?: string; path?: string }).parentPath
                    ?? (entry as { parentPath?: string; path?: string }).path
                    ?? srcRoot;

    if (target === 'claude' || target === 'opencode') {
      // .claude/skills/<slug>/...    or    .opencode/skills/<slug>/...
      const rel = relative(srcRoot, parentPath);
      const parts = rel.split(/[/\\]/);
      const skillsIdx = parts.findIndex((p) => p === 'skills');
      if (skillsIdx >= 0 && parts.length > skillsIdx + 1) {
        slugs.add(parts[skillsIdx + 1]);
      }
    } else if (target === 'roo') {
      // .roo/rules/<NN>-<slug>.md or .roo/rules/<NN>-<slug>-ref-...
      const m = entry.name.match(/^\d{2}-([a-z0-9-]+?)(?:-ref|\.md$)/);
      if (m) slugs.add(m[1]);
    }
  }

  return Array.from(slugs).sort();
}

// ─── Interactive prompts ────────────────────────────────────────────────

/**
 * Dual-mode prompter: uses Node's readline for TTY input (real users), and a
 * line-buffer fallback for piped/file stdin (scripted testing). Some Node and bun
 * versions close readline after the first `question()` call when stdin is non-TTY,
 * which makes a multi-prompt wizard impossible without the fallback.
 */
class Prompter {
  private readonly isTTY: boolean = process.stdin.isTTY === true;
  private readonly rl = this.isTTY ? createInterface({ input, output }) : null;
  private bufferedLines: string[] | null = null;
  private bufferIndex = 0;

  private async readLine(promptText: string): Promise<string> {
    if (this.rl) {
      return await this.rl.question(promptText);
    }
    // Non-TTY: lazy-load all of stdin once, then serve from the buffer.
    if (this.bufferedLines === null) {
      const chunks: Buffer[] = [];
      for await (const chunk of input) {
        chunks.push(chunk as Buffer);
      }
      this.bufferedLines = Buffer.concat(chunks).toString('utf-8').split('\n');
    }
    process.stdout.write(promptText);
    if (this.bufferIndex >= this.bufferedLines.length) {
      throw new Error('unexpected end of stdin while reading prompt input');
    }
    const line = this.bufferedLines[this.bufferIndex++];
    process.stdout.write(line + '\n');  // echo the line so the transcript is readable
    return line;
  }

  async select<T extends string>(
    label: string,
    options: Array<{ value: T; description?: string }>,
  ): Promise<T> {
    console.log();
    console.log(bold(label));
    options.forEach((opt, i) => {
      const num  = dim(`  ${i + 1})`);
      const val  = cyan(opt.value);
      const desc = opt.description ? dim(` — ${opt.description}`) : '';
      console.log(`${num} ${val}${desc}`);
    });
    while (true) {
      const ans = (await this.readLine(dim('  > '))).trim();
      const idx = parseInt(ans, 10);
      if (idx >= 1 && idx <= options.length) return options[idx - 1].value;
      const direct = options.find((o) => o.value === ans);
      if (direct) return direct.value;
      console.log(red(`  invalid; pick a number 1-${options.length} or type the value`));
    }
  }

  async input(label: string, defaultValue?: string): Promise<string> {
    console.log();
    console.log(bold(label));
    if (defaultValue) console.log(dim(`  (default: ${defaultValue})`));
    const ans = (await this.readLine(dim('  > '))).trim();
    return ans || defaultValue || '';
  }

  async confirm(label: string, defaultValue: boolean = false): Promise<boolean> {
    const yn = defaultValue ? 'Y/n' : 'y/N';
    console.log();
    const ans = (await this.readLine(`${bold(label)} ${dim(`(${yn})`)} > `))
      .trim()
      .toLowerCase();
    if (ans === '') return defaultValue;
    return ans === 'y' || ans === 'yes';
  }

  close(): void {
    if (this.rl) this.rl.close();
  }
}

// ─── Wizard ─────────────────────────────────────────────────────────────

interface WizardResult {
  target: Target;
  dest: string;
  skill: string | null;  // null = all
  dryRunFirst: boolean;
  force: boolean;
}

async function runWizard(): Promise<WizardResult> {
  console.log();
  console.log(bold(cyan('  ai-skills installer')));
  console.log(dim('  install one or more built skills into a destination project'));
  console.log();

  const p = new Prompter();
  try {
    const target = await p.select<Target>(
      'Which target tool?',
      TARGETS.map((t) => ({ value: t, description: TARGET_DESCRIPTIONS[t] })),
    );

    const dest = await p.input('Destination project root (path):');
    if (!dest) throw new Error('destination is required');

    let skill: string | null = null;
    if (target === 'codex') {
      console.log(dim('\n  (codex installs all skills as a single AGENTS.md — no per-skill filter)'));
    } else {
      const skills = await discoverSkills(target);
      if (skills.length === 0) {
        console.log(yellow(`\n  no skills found under dist/${target}/ — did you run the build?`));
      } else if (skills.length === 1) {
        console.log(dim(`\n  only one skill available: ${skills[0]}`));
        skill = skills[0];
      } else {
        const choice = await p.select<string>(
          'Install which skill(s)?',
          [
            { value: '*', description: `all available skills (${skills.join(', ')})` },
            ...skills.map((s) => ({ value: s, description: '' })),
          ],
        );
        skill = choice === '*' ? null : choice;
      }
    }

    const dryRunFirst = await p.confirm('Show a dry-run preview before writing?', true);
    const force       = await p.confirm('Overwrite existing files at the destination if they conflict?', false);

    return { target, dest, skill, dryRunFirst, force };
  } finally {
    p.close();
  }
}

// ─── Core install operation ─────────────────────────────────────────────

interface InstallOptions {
  target: Target;
  dest: string;
  skill: string | null;
  dryRun: boolean;
  force: boolean;
}

async function performInstall(opts: InstallOptions): Promise<number> {
  const srcRoot  = join(DIST_DIR, opts.target);
  const destRoot = resolve(expandHome(opts.dest));

  let pairs: Array<[string, string]>;
  try {
    pairs = await iterInstallFiles(srcRoot, opts.skill);
  } catch (e) {
    console.error(red(`error: ${(e as Error).message}`));
    return 2;
  }

  if (pairs.length === 0) {
    if (opts.skill) {
      console.error(red(`no files for skill ${JSON.stringify(opts.skill)} under ${srcRoot}`));
    } else {
      console.error(red(`no files under ${srcRoot}`));
    }
    return 1;
  }

  if (opts.dryRun) {
    console.log(yellow(`DRY RUN — would copy ${pairs.length} file(s) from ${srcRoot} to ${destRoot}:`));
    for (const [, rel] of pairs) {
      console.log(`  ${join(destRoot, rel)}`);
    }
    return 0;
  }

  if (!(await exists(destRoot))) {
    console.error(red(`error: destination ${destRoot} does not exist`));
    return 2;
  }
  if (!(await isDirectory(destRoot))) {
    console.error(red(`error: destination ${destRoot} is not a directory`));
    return 2;
  }

  let written = 0;
  let skipped = 0;
  for (const [src, rel] of pairs) {
    const destFile = join(destRoot, rel);
    if (await exists(destFile)) {
      if (!opts.force) {
        console.log(yellow(`SKIP ${rel} (exists; use --force to overwrite)`));
        skipped++;
        continue;
      }
    }
    await mkdir(dirname(destFile), { recursive: true });
    await copyFile(src, destFile);
    console.log(green(`COPY ${rel}`));
    written++;
  }

  console.log();
  console.log(`${written} file(s) written, ${skipped} skipped`);
  return 0;
}

// ─── Argument parsing ───────────────────────────────────────────────────

interface CliArgs {
  target: Target | null;
  dest: string | null;
  skill: string | null;
  dryRun: boolean;
  force: boolean;
  interactive: boolean;
  help: boolean;
}

function parseCliArgs(): CliArgs {
  const { values } = parseArgs({
    args: process.argv.slice(2),
    options: {
      target:      { type: 'string',  short: 't' },
      dest:        { type: 'string',  short: 'd' },
      skill:       { type: 'string',  short: 's' },
      'dry-run':   { type: 'boolean' },
      force:       { type: 'boolean', short: 'f' },
      interactive: { type: 'boolean', short: 'i' },
      help:        { type: 'boolean', short: 'h' },
    },
    strict: true,
    allowPositionals: false,
  });

  const target = values.target ?? null;
  if (target !== null && !(TARGETS as readonly string[]).includes(target)) {
    throw new Error(`invalid --target: ${target} (valid: ${TARGETS.join(', ')})`);
  }

  return {
    target:      target as Target | null,
    dest:        values.dest ?? null,
    skill:       values.skill ?? null,
    dryRun:      values['dry-run'] ?? false,
    force:       values.force ?? false,
    interactive: values.interactive ?? false,
    help:        values.help ?? false,
  };
}

function printHelp(): void {
  console.log(`
Install built skills into a destination project.

Usage:
  install.ts                                      (interactive wizard if no args)
  install.ts --target <t> --dest <path> [opts]    (non-interactive)

Options:
  -t, --target <t>      claude | opencode | roo | codex
  -d, --dest <path>     destination project root (~ expanded)
  -s, --skill <slug>    install only this skill (claude/opencode/roo only)
      --dry-run         list what would be copied; write nothing
  -f, --force           overwrite existing files at the destination
  -i, --interactive     force the interactive wizard
  -h, --help            show this help

Examples:
  install.ts                                                  (wizard)
  install.ts -t claude -d ~/my-project
  install.ts -t claude -d ~/my-project -s database-access
  install.ts -t claude -d ~/my-project --dry-run
  install.ts -t codex  -d ~/my-project --force

Run this script with one of:
  bun scripts/install.ts ...
  node --experimental-strip-types scripts/install.ts ...    (Node 22+)
  npx tsx scripts/install.ts ...
`.trimStart());
}

// ─── Main ───────────────────────────────────────────────────────────────

async function main(): Promise<number> {
  let args: CliArgs;
  try {
    args = parseCliArgs();
  } catch (e) {
    console.error(red(`error: ${(e as Error).message}`));
    console.error(dim('run with --help for usage'));
    return 2;
  }

  if (args.help) {
    printHelp();
    return 0;
  }

  // Wizard mode: explicit `--interactive`, OR no args at all.
  const noArgsGiven =
    !args.target && !args.dest && !args.skill && !args.dryRun && !args.force && !args.interactive;

  if (args.interactive || noArgsGiven) {
    let wizard: WizardResult;
    try {
      wizard = await runWizard();
    } catch (e) {
      console.error(red(`error: ${(e as Error).message}`));
      return 2;
    }

    if (wizard.dryRunFirst) {
      const code = await performInstall({
        target: wizard.target,
        dest:   wizard.dest,
        skill:  wizard.skill,
        dryRun: true,
        force:  wizard.force,
      });
      if (code !== 0) return code;

      const p = new Prompter();
      const proceed = await p.confirm('Proceed with the actual install?', false);
      p.close();
      if (!proceed) {
        console.log(dim('aborted'));
        return 0;
      }
    }

    return performInstall({
      target: wizard.target,
      dest:   wizard.dest,
      skill:  wizard.skill,
      dryRun: false,
      force:  wizard.force,
    });
  }

  // Non-interactive: validate required args.
  if (!args.target) {
    console.error(red('error: --target is required (or run with no args for the wizard)'));
    return 2;
  }
  if (!args.dest) {
    console.error(red('error: --dest is required (or run with no args for the wizard)'));
    return 2;
  }

  return performInstall({
    target: args.target,
    dest:   args.dest,
    skill:  args.skill,
    dryRun: args.dryRun,
    force:  args.force,
  });
}

main()
  .then((code) => process.exit(code))
  .catch((err: Error) => {
    console.error(red(`fatal: ${err.message}`));
    process.exit(1);
  });
