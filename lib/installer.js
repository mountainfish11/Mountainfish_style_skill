const fs = require('fs');
const path = require('path');
const os = require('os');

// Paths
const PACKAGE_ROOT = path.resolve(__dirname, '..');
const CLAUDE_DIR = path.join(os.homedir(), '.claude');
const COMMANDS_TARGET = path.join(CLAUDE_DIR, 'commands', 'mountainfish');
const SKILLS_TARGET = path.join(CLAUDE_DIR, 'skills', 'mountainfish');
const MEMORY_TARGET = path.join(SKILLS_TARGET, 'memory');
const REFERENCE_TARGET = path.join(SKILLS_TARGET, 'reference');

// Source paths
const COMMANDS_SOURCE = path.join(PACKAGE_ROOT, 'commands');
const SKILLS_SOURCE = path.join(PACKAGE_ROOT, 'skills', 'mountainfish');

function copyDirSync(src, dest) {
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }

  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      // Skip __pycache__ and .git
      if (entry.name === '__pycache__' || entry.name === '.git') {
        continue;
      }
      copyDirSync(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function removeDirSync(dir) {
  if (fs.existsSync(dir)) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

async function install(options = {}) {
  const { silent = false } = options;

  if (!silent) {
    console.log('Installing Mountainfish skill for Claude Code...\n');
  }

  // Create directories
  fs.mkdirSync(COMMANDS_TARGET, { recursive: true });
  fs.mkdirSync(SKILLS_TARGET, { recursive: true });
  fs.mkdirSync(MEMORY_TARGET, { recursive: true });
  fs.mkdirSync(REFERENCE_TARGET, { recursive: true });

  // Copy commands
  if (!silent) {
    console.log('  Copying commands...');
  }
  copyDirSync(COMMANDS_SOURCE, COMMANDS_TARGET);

  // Copy scripts, memory and reference
  if (!silent) {
    console.log('  Copying scripts, memory and reference...');
  }
  copyDirSync(SKILLS_SOURCE, SKILLS_TARGET);

  if (!silent) {
    console.log('\nInstallation complete!\n');
    console.log('Installed to:');
    console.log(`  Commands: ${COMMANDS_TARGET}`);
    console.log(`  Skills:   ${SKILLS_TARGET}`);
    console.log('\nAvailable commands in Claude Code:');
    console.log('  /mountainfish_start     - Load memory at session start');
    console.log('  /mountainfish_inject    - Manually inject specific experience');
    console.log('  /mountainfish_integrate - Integrate experience to memory bank');
    console.log('  /mountainfish_profiling - Analyze project coding style');
    console.log('\nRun "mountainfish status" to verify installation.');
  }
}

async function uninstall() {
  console.log('Uninstalling Mountainfish skill...\n');

  removeDirSync(COMMANDS_TARGET);
  removeDirSync(REFERENCE_TARGET);
  removeDirSync(SKILLS_TARGET);

  // Remove parent dirs if empty
  const commandsParent = path.dirname(COMMANDS_TARGET);
  const skillsParent = path.dirname(SKILLS_TARGET);

  try {
    fs.rmdirSync(commandsParent);
  } catch (e) { /* not empty */ }

  try {
    fs.rmdirSync(skillsParent);
  } catch (e) { /* not empty */ }

  console.log('Uninstallation complete.');
}

async function status() {
  console.log('Mountainfish Installation Status\n');

  const commandsExist = fs.existsSync(COMMANDS_TARGET);
  const skillsExist = fs.existsSync(SKILLS_TARGET);
  const scriptsExist = fs.existsSync(path.join(SKILLS_TARGET, 'scripts'));

  // Check command files
  const commandFiles = commandsExist
    ? fs.readdirSync(COMMANDS_TARGET).filter(f => f.endsWith('.md'))
    : [];

  // Count memory files
  const memoryDir = path.join(MEMORY_TARGET);
  const memoryFiles = fs.existsSync(memoryDir)
    ? fs.readdirSync(memoryDir).filter(f => f.endsWith('.md'))
    : [];

  // Count reference files
  const referenceDir = path.join(REFERENCE_TARGET);
  const referenceFiles = fs.existsSync(referenceDir)
    ? fs.readdirSync(referenceDir).filter(f => f.endsWith('.md'))
    : [];

  // Display status
  console.log(`Commands directory: ${commandsExist ? 'OK' : 'MISSING'} (${COMMANDS_TARGET})`);
  console.log(`  Command files: ${commandFiles.length > 0 ? commandFiles.join(', ') : 'none'}`);
  console.log(`Skills directory: ${skillsExist ? 'OK' : 'MISSING'} (${SKILLS_TARGET})`);
  console.log(`  Scripts: ${scriptsExist ? 'OK' : 'MISSING'}`);
  console.log(`  Memory files: ${memoryFiles.length}`);
  console.log(`  Reference files: ${referenceFiles.length}`);

  if (commandsExist && skillsExist && scriptsExist) {
    console.log('\nStatus: INSTALLED');
  } else {
    console.log('\nStatus: NOT INSTALLED');
    console.log('Run "mountainfish install" to install.');
  }
}

module.exports = { install, uninstall, status };
