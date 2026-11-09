---
name: re-playbook
description: Reverse engineering playbook: method, tool stack and a deep reference (PE/ELF/Mach-O, ABIs, protectors, ROP, Frida, angr). Use for binary analysis, packers, malware triage, firmware and mobile apps.
---

# re-playbook

Authorized work only: your own software, CTFs, malware triage in an isolated environment, interoperability and security research you are permitted to do.

## Method
1. Static triage first: file format, architecture, imports, strings, entropy, packing indicators.
2. Control-flow analysis: basic blocks, CFG, branches, loops, indirect calls.
3. Data-flow analysis: backward slice from a result, forward trace from an input.
4. Treat the decompiler as a hypothesis generator. Verify critical paths in the disassembly.
5. Confirm dynamically: breakpoints, registers and memory at runtime. Run unknown samples only in an isolated VM.
6. Build a compiler-pattern library: how if, switch, loop, vtable, array and string look in assembly.
7. Packers: find the original entry point, trace the runtime restoration, dump and fix imports.
8. Drivers: entry points, dispatch routines, IOCTL interfaces, IRQL context.
9. Virtualized code: find the dispatcher, map the handlers, reconstruct the virtual ISA.

State what is verified (read in the disassembly or observed at runtime) versus believed. A decompiler listing alone is believed.

## Tool stack (use what is installed)
| Tool | Use for |
| --- | --- |
| IDA Pro MCP | Static analysis, patching bytes, decompilation, xrefs, imports, structs |
| REA | Open binaries, decompile, search strings, xrefs, procedure analysis, browser and Android targets |
| Ghidra with an MCP bridge | Decompile, data-flow tracing, diffing, renaming, structures, call graphs |
| radare2 | Terminal-based analysis |
| Frida | Dynamic instrumentation: hook functions, trace calls, inspect memory |
| jadx | Android APK and DEX decompilation |

## Deep reference
Load `references/re-reference.md` only when you need a specific topic: commercial protectors, ARM/AArch64, Frida scripting, Windows and ELF and macOS internals, debugger cheat sheets, ROP, shellcode patterns, PE format, memory forensics, angr patterns, Windows x64 and System V ABIs.
