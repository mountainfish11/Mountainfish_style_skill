#!/usr/bin/env node

const { install, uninstall, status } = require('../lib/installer');
const path = require('path');

const args = process.argv.slice(2);
const command = args[0];

const HELP = `
mountainfish - Claude Code knowledge accumulation skill

Usage:
  mountainfish install    Install skill to ~/.claude/
  mountainfish uninstall  Remove skill from ~/.claude/
  mountainfish status     Check installation status
  mountainfish help       Show this help

After installation, use these commands in Claude Code:
  /mountainfish_start     Load memory at session start
  /mountainfish_inject    Manually inject specific experience
  /mountainfish_integrate Integrate experience to memory bank
  /mountainfish_profiling Analyze project coding style
`;

async function main() {
  try {
    switch (command) {
      case 'install':
        const isSilent = args.includes('--silent');
        await install({ silent: isSilent });
        break;

      case 'uninstall':
        await uninstall();
        break;

      case 'status':
        await status();
        break;

      case 'help':
      case '--help':
      case '-h':
        console.log(HELP);
        break;

      default:
        if (command) {
          console.error(`Unknown command: ${command}`);
        }
        console.log(HELP);
        process.exit(command ? 1 : 0);
    }
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

main();
