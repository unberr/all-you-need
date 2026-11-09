# Reverse engineering reference

### RE methodology
1. Static triage first: file format, arch, imports, strings, entropy, packing indicators
2. Control-flow analysis: basic blocks, CFG, branches, loops, indirect calls
3. Data-flow analysis: backward slice from result, forward trace from input
4. Decompiler as hypothesis generator — verify critical paths in disassembly
5. Dynamic confirmation: set breakpoints, check registers/memory at runtime
6. Build compiler-pattern library: if/switch/loop/vtable/array/string in assembly
7. For packers: find OEP, trace runtime restoration, dump + fix imports
8. For drivers: entry points, dispatch routines, IOCTL interfaces, IRQL context
9. For virtualized code: find dispatcher, map handlers, reconstruct virtual ISA

### Deep RE — iceberg layers

**Compiler internals**
- LLVM IR / GCC GIMPLE: understand how source becomes machine code
- Register allocation (graph coloring), instruction scheduling, loop unrolling
- Link-time optimization (LTO) merges functions across translation units — xrefs lie
- PGO (profile-guided optimization) produces branch layouts based on training data, not logic

**Anti-analysis techniques**
- Timing attacks: `RDTSC` delta checks detect single-step debugging
- `IsDebuggerPresent`, `NtQueryInformationProcess`, heap flag checks, TLS callbacks before OEP
- Exception-based control flow: `SEH`/`VEH` used as unconditional jumps
- Self-modifying code: `.text` section marked writable, decrypts itself per-call
- Junk bytes / overlapping instructions: disassembler desyncs, real code starts mid-instruction
- Control flow flattening (Obfuscator-LLVM): every block dispatched through a state machine
- Opaque predicates: always-true/false branches that look conditional

**Packer internals**
- IAT reconstruction: `GetProcAddress` called at runtime, IAT rebuilt in scratch memory
- Section stomping: legitimate section header replaced, payload injected
- Process hollowing: spawn suspended process, unmap its image, map payload
- Reflective DLL injection: PE loader inside the DLL itself, no `LoadLibrary`
- Manual mapping: map sections, apply relocations, resolve imports, call DllMain — all in userland
- TLS callback execution before entry point: code runs before debugger OEP break

**Virtualized protection (VM-based obfuscation)**
- Identify: single dispatcher loop + large handler table = VM
- Map virtual registers → native registers via dynamic trace
- Extract bytecode: find fetch-decode-dispatch loop, dump bytecode stream
- Reconstruct ISA: each handler = one virtual opcode; build opcode→semantic table
- Tools: `VMAttack` (IDA plugin), `VMP2Clang`, manual symbolic execution via angr
- Targets: VMProtect, Themida, Code Virtualizer, custom game anticheat VMs

**Kernel / hypervisor**
- DKOM (Direct Kernel Object Manipulation): unlink EPROCESS from list → process invisible
- PatchGuard: periodic integrity checks on kernel structures; triggers BSOD if patched
- HVCI (Hypervisor-Protected Code Integrity): kernel pages enforced by hypervisor, not OS
- VT-x EPT hooks: shadow page tables redirect reads vs executes to different physical pages
- Syscall hooking via `LSTAR` MSR (bare metal) vs SSDT hooks (legacy)
- Hyper-V enlightenments: guest OS uses hypercalls instead of emulated hardware

**Firmware / bootkit**
- UEFI DXE driver persistence: dropped to SPI flash, survives OS reinstall
- MBR/VBR bootkits: hooks int 13h, patches bootloader in memory before kernel loads
- SMM (System Management Mode): ring -2, invisible to OS, triggered by SMI; hardest to detect
- Measured boot / TPM PCR chain: each boot stage hashes next; attestation fails if tampered
- ACPI AML bytecode: interpreted by OS, can contain malicious logic

**Symbolic execution / automated analysis**
- angr: `proj.factory.simgr()`, `explore(find=addr, avoid=addr)` to reach target path
- Concolic: concrete execution + symbolic constraints; Z3 solver finds inputs
- Taint tracking: mark attacker-controlled bytes, trace to sensitive sinks
- Binary diffing: BinDiff / Diaphora — match functions across versions by CFG similarity
- Coverage-guided fuzzing: AFL++ with QEMU mode for closed-source binaries

**Protocol RE**
- Identify framing: length-prefixed vs delimiter-based vs fixed-size messages
- Entropy analysis per field: high = encrypted/compressed, low = structured data
- Differential inputs: send known inputs, observe field changes in Wireshark + Frida simultaneously
- TLS interception: Frida hook `SSL_read`/`SSL_write` before encryption layer

### Commercial protectors — internals & analysis

**UPX (Ultimate Packer for eXecutables)**
- Most common packer; open-source, well understood
- Signature: `UPX0`/`UPX1` section names, `UPX!` magic at end of file
- Unpack: `upx -d binary.exe` works on unmodified UPX; malware often corrupts headers to break this
- If headers corrupted: find OEP manually — look for `pushad` near start, then `popad; jmp <OEP>` pattern (tail jump); dump at OEP with `pe-sieve` or x64dbg Scylla plugin
- Stub layout: compressed data in UPX1, decompressor in UPX0, original IAT rebuilt at runtime
- Detection: `die` (Detect It Easy) fingerprints instantly; entropy of UPX1 ~7.9 (near max)

**VMProtect internals**
- Two modes: *Mutation* (junk/substitution, no VM) and *Virtualization* (full VM, hardest)
- Mutation: opaque predicates + junk insertion + MBA (Mixed Boolean-Arithmetic) substitution; strip with symbolic execution or LLVM optimization passes
- VM structure: `PUSH <bytecode_ptr>` → call dispatcher; dispatcher = fetch opcode → index handler table → execute handler → loop
- Each build randomizes: handler order, virtual register mapping, opcode values — no two builds look alike
- Analysis approach:
  1. Identify VM entry: single call with large data blob argument
  2. Find dispatch loop: indirect `jmp [rax*8 + handler_table]` pattern
  3. Trace with PIN/Frida to log (vPC, handler_addr) pairs → build opcode→handler map
  4. Lift handlers to IR (use miasm or VMP2LLVM), fold constants, dead-code eliminate
  5. Reconstruct CFG from lifted IR
- Tools: `VMAttack` (IDA plugin, older VMP versions), `VMP2Clang`, `miasm`, manual angr
- Key weakness: VM I/O still touches real OS via `call [import]` — trace at API boundary regardless of VM internals

**Themida / WinLicense internals**
- Oreans protector; layers: compression → encryption → anti-debug → optional VM (Themida SDK macros)
- Anti-debug arsenal: `IsDebuggerPresent`, `NtQueryInformationProcess` (ProcessDebugPort), heap flags (`NtGlobalFlag`), `OutputDebugString` timing, `RDTSC` delta, parent PID check, `CheckRemoteDebuggerPresent`
- Anti-dump: corrupts PE header in memory (`SizeOfImage`, section headers zeroed after unpack)
- Anti-attach: watchdog thread calls `NtQueryInformationProcess` in loop; exits process on debugger detect
- Bypass strategy:
  1. ScyllaHide plugin for x64dbg/IDA — patches all standard anti-debug checks at once
  2. `NtSetInformationThread(ThreadHideFromDebugger)` check: ScyllaHide handles; manual patch: hook `NtQueryInformationProcess` return 0 for `ProcessDebugPort`
  3. Dump: let run to OEP, use `pe-sieve /pid` to dump clean; fix IAT with Scylla
  4. If VM sections present: treat same as VMProtect VM analysis

**Denuvo anti-tamper**
- Not a packer — wraps existing binary with integrity checks + online activation
- Architecture: VM triggers (~3000 per protected binary) inserted at "sensitive" basic blocks; each trigger calls Denuvo runtime which checks: CPU fingerprint (CPUID), disk serial, MAC address, online token
- Offline token: 72h validity baked in; renewed on each game launch if online
- RE difficulty: each game build has unique VM with different handler layouts; no two Denuvo-protected binaries share bytecode
- Analysis approach: identify VM entry points via entropy spikes + unusual `call` patterns; trace execution to understand trigger conditions; known weakness is that most content executes *outside* the VM — game logic is unprotected, only startup/DRM checks are inside VM
- Academic status: fully reversed by scene groups; methods not publicly documented but known to involve hardware-bound token replay + VM devirtualization for trigger removal

**Enigma Protector**
- Similar architecture to Themida; adds custom VM + registry/file-based license storage
- License check typically: read encrypted blob from registry/file → decrypt with embedded key → verify HMAC → compare machine fingerprint
- Find license check: xref from registry read APIs (`RegQueryValueEx`) → trace forward to comparison → patch `jnz→jmp` or zero out HMAC verify

**Code Virtualizer / Obsidium / ASProtect**
- Code Virtualizer: Oreans light VM (same family as Themida); fewer anti-debug tricks
- Obsidium: PE protector with strong anti-debug + import hiding; find OEP via hardware breakpoint on stack (`esp-4`) at entry
- ASProtect: older, common in legacy software; known OEP-finding technique: `bpx LoadLibraryA` then trace until tail jump

**General packer/protector workflow**
1. Identify protector: `die`/`PEiD`/`ExeinfoPE` — fingerprint by section names, entry point byte patterns, overlay signatures
2. Entropy analysis: `binwalk -E` or `die` — high entropy sections = compressed/encrypted
3. Find OEP (manual if needed):
   - Hardware BP on stack pointer at entry (`ESP` trick: `pushad` saves regs → note ESP → HBP on [ESP-4] → `popad; jmp OEP`)
   - Or: `bpx VirtualAlloc` / `VirtualProtect` — protector allocates+unpacks to new region, then jumps
4. Dump: `pe-sieve /pid <pid> /dump 3` — dumps all PE images from process memory, fixes headers
5. IAT reconstruction: Scylla (x64dbg plugin) — scan for imports, rebuild IAT, fix dump
6. Anti-debug bypass before OEP: ScyllaHide mandatory; also patch `KiUserExceptionDispatcher` hook for SEH-based tricks

**Anti-debug cheat sheet (all known checks)**
| Check | Location | Bypass |
|---|---|---|
| `IsDebuggerPresent` | PEB+0x2 BeingDebugged | Patch PEB byte to 0 |
| `NtQueryInformationProcess(ProcessDebugPort)` | ntdll | Hook → return 0 |
| `NtQueryInformationProcess(ProcessDebugObjectHandle)` | ntdll | Hook → return STATUS_PORT_NOT_SET |
| `CheckRemoteDebuggerPresent` | kernel32 | Same hook as above |
| `NtGlobalFlag` PEB+0xBC | PEB | Patch to 0 (default: 0x70 when debugged) |
| Heap flags (`ForceFlags`) | heap header | Patch heap flags |
| `RDTSC` delta | inline | Patch with NOPs or hook `RDTSC` |
| Parent PID check | NtQueryInformationProcess(ProcessBasicInfo) | Hook → return real parent |
| `OutputDebugString` error check | GetLastError after call | NOP the check |
| Timing (GetTickCount delta) | inline | Hook GetTickCount → constant |
| `CloseHandle(invalid_handle)` | inline | 0xC0000008 exception = debugger present; ScyllaHide handles |
| Hardware breakpoint check (DR registers) | NtGetContextThread | Hook → zero DR0-DR7 |
| `NtSetInformationThread(ThreadHideFromDebugger)` | ntdll | Hook → NOP |
| Vectored exception handler TLS check | TLS callbacks | Set BP before OEP |

**Import hiding / IAT obfuscation**
- `GetProcAddress` at runtime → store in local var → call through pointer: static disasm shows `call rax`, not function name
- API hashing: hash function name (DJB2/CRC32) → iterate exports → compare → resolve; find hash function by xref from import loop
- Manual map (no LoadLibrary): locate PEB→Ldr→InMemoryOrderModuleList → walk exports manually; invisible to `lsof`/`Process Hacker` import tab
- Stomped imports: legitimate DLL exports overwritten in memory post-load; original export still on disk — compare memory vs disk with `pe-sieve`

### Abyss-level RE — elite knowledge

**CPU microarchitecture exploitation**
- Spectre/Meltdown class: branch predictor poisoning leaks cross-privilege memory via cache timing
- Rowhammer: flip DRAM bits by repeated read of adjacent rows — no code execution required
- Microcode patching: Intel/AMD microcode loaded at boot; NSA-class adversaries patch it; survives reflash
- CPU errata: undocumented instruction behaviors used as covert channels or sandbox escapes
- TSX (Intel Transactional Synchronization): abort handler used for stealthy code execution without traces
- Prefetch side-channel: `PREFETCH` instruction timing reveals kernel ASLR slide from userland

**Hypervisor-level stealth (ring -1)**
- Blue Pill / Azazel class: install hypervisor under running OS, OS becomes guest — transparent to OS-level tools
- EPT violation hooks: hook execution without modifying target page; read returns original bytes, execute runs hook
- VMCS shadowing: nested hypervisor can intercept guest hypervisor's VMCS reads/writes
- `CPUID` spoofing: hypervisor intercepts CPUID, returns falsified hardware/feature data to guest
- `RDMSR`/`WRMSR` intercepts: monitor or manipulate MSR reads silently from hypervisor
- Covert channel via shared cache: hypervisor and guest communicate via LLC eviction patterns

**SMM (ring -2) implants — Equation Group / Fancy Bear level**
- SMI handler injection: modify SMRAM content before SMRAM lock; persist through OS reinstall and reflash
- SPI flash write via SMM: bypasses SPI write-protect by executing in SMM context where WP is lifted
- `EFI_SMM_BASE2_PROTOCOL` abuse: register malicious SMI handler as legitimate UEFI SMM driver
- ThunderStrike / DarkMatter class: exploit Option ROM execution during boot to install EFI implant
- SMRAM overlap attack: map SMRAM into DMA-accessible region, inject via PCIe DMA before lock

**Hardware implants / interdiction**
- PCIe DMA attack: rogue PCIe device issues DMA to arbitrary physical addresses — bypasses all software
- JTAG/SWD persistence: plant code via debug interface, lock fuses, disable debug port after
- Supply chain: implant in BMC (Baseboard Management Controller) firmware. Documented case: the iLOBleed rootkit in HPE iLO (2021). Bloomberg's 2018 Supermicro hardware-implant report is disputed and unconfirmed: do not cite it as an established attack
- Acoustic/EM side-channel: reconstruct RSA private key from CPU electromagnetic emissions during decryption
- Power analysis (DPA): statistical analysis of power consumption during crypto = key extraction without code access

**Anti-forensic / trace erasure**
- Kernel log suppression: hook `DbgPrint` / `WMI` / `ETW` provider registration to drop events before they write
- ETW patching: NOP the `EtwEventWrite` syscall stub in ntdll — telemetry blind
- MFT record manipulation: modify `$MFT` directly via raw disk access, timestamps + records altered
- Hibernation file manipulation: `hiberfil.sys` contains full RAM snapshot — sanitize before sleep
- Pagefile scrubbing: sensitive data in `pagefile.sys`; zero via `NtSetSystemInformation(SystemMemoryListInformation)`
- USN Journal poisoning: NTFS change journal entries forged or deleted to erase file activity

**Advanced binary analysis — academic/elite**
- Abstract interpretation: over-approximate all possible program states without execution (used in SLAM, Astrée)
- Points-to analysis (Andersen/Steensgaard): statically resolve what pointers can point to — powers precise taint
- Satisfiability Modulo Theories (SMT): Z3, Bitwuzla — encode program semantics as formulas, solve for inputs
- Program synthesis: given input/output pairs, synthesize the function — deobfuscation without manual analysis
- Behavioral diffing: find where two binaries differ without full decompilation (BinDiff, Diaphora for structure; differential fuzzing or symbolic equivalence checking for behavior)
- Probabilistic disassembly (Miller et al., ICSE 2019): assign each address a probability of being an instruction start, so obfuscated x86 is disassembled without one hard guess
- Deobfuscation via LLVM: lift to LLVM IR, run optimization passes (instcombine, GVN, SCCP), lower back — strips opaque predicates

**Cryptographic RE**
- AES key recovery: no practical attack recovers an AES key from observed ciphertexts. Related-key attacks on AES-192/256 (Biryukov-Khovratovich, 2009) are theoretical. In RE the key comes from the binary: the expanded key schedule in memory (round keys invert to the master key), white-box tables, or side channels
- RC4: broken for TLS by keystream biases (RFC 7465), but recovering the full internal state from keystream alone is still impractical. Recover the key from the binary instead
- Custom PRNG reverse: collect output sequence, solve for seed via Z3 or Berlekamp-Massey
- Hash length extension: SHA-1, SHA-256, SHA-512 used as `H(secret || message)` (not HMAC) — extend the message without knowing the secret. SHA-3 and truncated variants (SHA-512/256, SHA-384) resist it
- Padding oracle attacks: an error or timing difference on bad padding decrypts byte by byte (Vaudenay 2002 for CBC; Bleichenbacher 1998 for RSA PKCS#1 v1.5)
- White-box cryptography analysis: AES key embedded in lookup tables — DFA (Differential Fault Analysis) extracts it

**Covert channels & exfiltration (nation-state class)**
- DNS covert channel: data exfil via subdomain queries — bypasses egress firewall
- ICMP tunnel: payload in echo request/reply — Loki2 class
- Steganography in network timing: encode bits in inter-packet delay — no payload inspection catches it
- CPU cache covert channel: Flush+Reload between processes sharing a page — no network required
- Ultrasonic covert channel (AirHopper): air-gapped machine exfils via speaker→mic ultrasound
- Power-line covert channel (PowerHammer): air-gapped machine modulates power consumption → read from power line

**RE of protection systems (anticheat / DRM / EDR)**
- Kernel callbacks enumeration: `PsSetCreateProcessNotifyRoutine`, `ObRegisterCallbacks`, `CmRegisterCallback` — map all hooks
- Minifilter driver stack: enumerate all filesystem filter drivers, identify EDR interception layers
- ETW provider enumeration: list all registered providers, identify security telemetry sources
- Handle table walk: enumerate all process handles kernel-side — bypasses `NtQuerySystemInformation` hooks
- DKOM PatchGuard bypass: modify protected structures during PatchGuard's own verification window (race)
- Hypervisor-based anticheat (BE/EAC): they run as VT-x hypervisors; defeating requires nested virt or hardware

### Bleeding edge 2024–2025 research (current state of the art)

**TEE / confidential computing broken (2024–2025)**
- **BadRAM** (CVE-2024-21944, Dec 2024): Manipulate DDR4/DDR5 SPD metadata to alias physical memory — breaks AMD SEV-SNP attestation, Intel TDX, SGX. $10 hardware. PoC: https://badram.eu/badram.pdf
- **Battering RAM** (Sep 2025, KU Leuven): $50 DIMM interposer, inserts memory aliases *at runtime* bypassing boot-time alias checks — defeats Intel TDX + AMD SEV-SNP firmware mitigations post-BadRAM
- **TEE.Fail** (Oct 2025, Georgia Tech/Purdue): DDR5 deterministic AES-XTS memory encryption side-channel — extracts SGX/TDX signing keys, forges attestation quotes. <$1000 hardware, root+physical required
- **HECKLER** (USENIX Security 2024): Inject controlled interrupts into AMD SEV-SNP and Intel TDX CVMs — breaks OpenSSH and sudo inside confidential VMs. CVE-2024-25744/25743. PoC: https://ahoi-attacks.github.io/heckler
- **TDXploit** (USENIX Security 2025): Single-step Intel TDX via APIC timer; RNG state recovery in 32 samples (per-core not per-TD); breaks cache side-channel mitigations
- **SnakeGX**: Framework to implant persistent backdoor into legitimate SGX enclaves — leaves minimal footprint
- Key insight: TEEs moved client→server hardware with DDR5 deterministic encryption = new physical side-channel surface

**Spectre / BPU attacks (2025)**
- **Spectre-BSE / Spectre-BHS / BiasScope** (USENIX Security 2025): 3 new primitives exploiting inaccurate branch history in BPU; BiasScope = cross-privilege control-flow side-channel using Branch Score Table (BST) as leakage oracle
- **BUSted** (IEEE S&P 2024): Microarchitectural side-channel on MCU *bus interconnect* — works on embedded/IoT CPUs without caches or speculative execution; defeats TEE on commercial MCUs
- **TONTOU** (2025): Bypasses Spectre v2 fixes — BTI attack across host/guest, leaks arbitrary memory from QEMU; fixed in Linux kernel via vBTI primitive
- **L1TF Reloaded** (VU Amsterdam 2025): L1 Terminal Fault + BTI combined on Coffee Lake — cloud cross-VM leakage
- BPU side-channels: measure branch execution time OR hardware performance counters (HPC) to infer BPU state; Pathfinder reverse-engineered Intel path history register (PHR) to extract AES key

**LLM-assisted binary analysis (2024–2025 frontier)**
- **Decompile-Bench** (NeurIPS 2025): 2M binary-source function pairs from 450GB of compiled GitHub code; fine-tuning on it = 20% improvement in re-executability. Used to advance LLM4Decompile. Repo: https://github.com/albertan017/LLM4Decompile
- **Idioms** (arxiv Feb 2025): Neural decompiler that jointly predicts code + user-defined type definitions; 54.4% accuracy on ExeBench — SOTA neural decompilation
- **DAILA** (mahaloz/DAILA): AI-assisted RE tool integrating LLMs into IDA/Ghidra workflow; human study shows LLMs save ~60s/function average
- **TYGR** (USENIX Security 2024): Type inference for decompiled code. Repo: https://github.com/sefcom/TYGR
- **Oxidizer** (2025): angr-based Rust decompiler generating semantically equivalent Rust pseudocode from binaries
- LLM deobfuscation limits: bogus control flow = easy for LLMs; CFF = moderate; instruction substitution + combined = LLMs *fail completely* (3-tier resistance model from DIMVA 2025)
- LLM + GNN ensemble (RAID 2025): combine CFG via GNN + assembly via LLM for binary function similarity; breaks CFF and VM obfuscation

**Hypervisor RE / analysis (2024–2025)**
- **Hyperpill** (USENIX Security 2024): Fuzzes hypervisors via hardware virtualization interface; snapshots hypervisor state via nested KVM, probes MMIO/PIO/DMA attack surface without device-specific grammars
- **The Reversing Machine (TRM)** (arxiv 2024): Hypervisor-based memory introspection using MBEC (Mode-Based Execution Control) to detect user/kernel transitions; transparent to evasive malware; 75% speedup in manual RE of kernel structures; detects threats 24 AV solutions miss

**Bootkit / UEFI persistence (2025)**
- **BootKitty** (WOOT 2025): First Linux bootkit bypassing Secure Boot, VBS, HVCI, PatchGuard, DSE simultaneously; uses LogoFAIL + CVE-2024-20865 to flash GPT without auth; exploits MOK to break chain of trust; studied via QEMU + Chipsec SPI flash dump
- Technique stack: UEFI bootkit → kernel rootkit → userland persistence: bypass each layer independently
- Chipsec (Intel tool): dump SPI flash regions for firmware analysis

**Hardware implants (NSA ANT Catalog + modern)**
- NSA ANT Catalog: leaked doc describing implants including one that attaches to server motherboard debug infrastructure (JTAG) to install CPU-level malware
- NSA Playset: open-source reimplementations of ANT Catalog attacks by hardware hackers
- Modern supply-chain threat: SPD manipulation (BadRAM) achievable via BMC/BIOS firmware update with Ring-0 access — no physical interposer required (AMD acknowledged: AV:L/AC:H/PR:H)
- PCB-level security: PCBA RE requires board-level reverse engineering; anti-RE: thick epoxy + X-ray-blocking material in epoxy

**Automated firmware RE (2024–2025)**
- P2IM, Firmadyne, Avatar2: firmware emulation for dynamic analysis without real hardware
- Chipsec: Intel firmware analysis framework; dumps SPI flash, checks SMRAM lock, verifies BIOS protections
- QEMU-based bootkit/rootkit analysis: boot into QEMU, attach GDB via `-s -S`, single-step UEFI DXE dispatch

**Windows kernel / anticheat bypass (academic 2024)**
- Vulnerable driver exploitation (BYOVD): load signed but vulnerable 3rd-party kernel driver, exploit it to get ring-0, bypass HVCI/PatchGuard; used by ransomware AND game cheats
- PatchGuard bypass window: BOOTKITTY disables VBS/HVCI before kernel loads = PatchGuard never starts
- Academic study (Univ. Birmingham 2024): strong correlation between anticheat strength and cheat price; cheat devs treat anticheat RE as economic optimization

### ARM / AArch64 RE

**Calling convention (AAPCS64)**
- Args: X0–X7 (integers/pointers), V0–V7 (floats/SIMD)
- Return: X0 (integer), V0 (float)
- Non-volatile: X19–X28, X29 (frame pointer), X30 (link register = return address)
- SP must be 16-byte aligned at call; no shadow space
- X16/X17 (IP0/IP1): intra-procedure scratch; used by PLT stubs — not preserved across calls
- X18: platform register (Windows ARM64: TEB; iOS: reserved; Linux: unused)

**A64 instruction encoding**
- Fixed 32-bit instruction width — disassemblers never desync (unlike x86)
- PC-relative addressing: `ADRP Xn, page` + `ADD Xn, Xn, #offset` = 4GB range; common for globals/strings
- `BL` = call (saves return addr in X30); `BLR Xn` = indirect call; `RET` = `BR X30`
- Condition codes on `CMP`/`TST` → `B.EQ`, `B.NE`, `B.LT`, `B.GT`, `B.LO`, `B.HI` (signed vs unsigned same as x86 jcc)
- `LDR`/`STR` with `[Xn, #imm]`, `[Xn, Xm, LSL #3]` — recognize array indexing
- `STP X29, X30, [SP, #-16]!` = function prologue (save frame ptr + link reg); `LDP X29, X30, [SP], #16` = epilogue

**PAC (Pointer Authentication) — iOS/macOS**
- `PACIBSP` at function entry: signs X30 (return addr) with SP as context → stored in upper bits of pointer
- `AUTIBSP` before `RET`: verifies signature; if tampered → crash (SIGILL or SIGSEGV)
- Breaks ROP chains: can't forge return address without key
- RE: in Ghidra/IDA, PAC instructions show as NOP on non-PAC hardware — ignore in static analysis; on real device, Frida can hook past PAC with `Interceptor.attach` (handles PAC transparently)
- `PACIZA`/`AUTIZA` = zero context variant; `PACDZA`/`AUTDZA` = data pointer auth

**BTI (Branch Target Identification)**
- `BTI` landing pad instruction at valid indirect branch targets
- Jump/call to non-BTI target → SIGILL; defeats JOP/COP chains
- RE: `BTI C` = valid call target; `BTI J` = valid jump target; `BTI JC` = both

**iOS/Android RE specifics**
- iOS: Mach-O format; `__TEXT/__text` = code, `__DATA/__data` = data, `__DATA_CONST` = const after fixup
- Objective-C: `objc_msgSend(id self, SEL op, ...)` — first two args always self+selector; find selectors in `__objc_selrefs`
- Swift: name-mangled symbols (`$s` prefix); `swift demangle` or `swift-demangle` tool to decode
- Android: ELF + JNI bridge; `Java_com_package_ClassName_methodName` = native method naming
- ART (Android Runtime): DEX bytecode JIT-compiled; Frida hooks Java layer OR native JNI layer
- `frida-objc-bridge`: hook ObjC methods by class+selector; `ObjC.classes.NSString["- stringWithFormat:"]`

---

### Frida scripting reference

**Core patterns**
```javascript
// Hook native function by address
Interceptor.attach(ptr("0x1400a1234"), {
  onEnter(args) {
    console.log("arg0:", args[0], "arg1:", args[1].readUtf8String());
  },
  onLeave(retval) {
    console.log("ret:", retval);
    retval.replace(ptr(1)); // force return value
  }
});

// Hook by export name
const fn = Module.getExportByName("kernel32.dll", "CreateFileW");
Interceptor.attach(fn, { onEnter(args) { console.log(args[0].readUtf16String()); } });

// Read/write memory
Memory.readByteArray(ptr("0x1400a1234"), 16);
Memory.writeByteArray(ptr("0x1400a1234"), [0x90, 0x90]);
ptr("0x1400a1234").readU32();
ptr("0x1400a1234").writeU64("0x1122334455667788");

// Scan memory for pattern
Memory.scan(Process.enumerateRanges('r-x')[0].base, 0x10000,
  "48 8B 05 ?? ?? ?? ??",  // wildcard bytes = ??
  { onMatch(addr) { console.log("found at", addr); } }
);

// Stalk (trace every instruction in thread)
Stalker.follow(Process.getCurrentThreadId(), {
  events: { call: true, ret: false, exec: false },
  onReceive(events) {
    const parsed = Stalker.parse(events);
    parsed.forEach(e => console.log(e[0], e[1].toString(16)));
  }
});

// Enumerate modules + exports
Process.enumerateModules().forEach(m => console.log(m.name, m.base, m.size));
Module.enumerateExports("ntdll.dll").forEach(e => console.log(e.name, e.address));

// Hook ObjC method (iOS/macOS)
const cls = ObjC.classes.NSURLSession;
const method = cls["- dataTaskWithRequest:completionHandler:"];
Interceptor.attach(method.implementation, {
  onEnter(args) {
    const req = new ObjC.Object(args[2]);
    console.log(req.URL().absoluteString());
  }
});

// Hook Java method (Android)
Java.perform(() => {
  const Activity = Java.use("android.app.Activity");
  Activity.onCreate.implementation = function(bundle) {
    console.log("onCreate called");
    this.onCreate(bundle);
  };
});
```

**Frida CLI**
```bash
frida -U -f com.app.package -l script.js   # spawn + inject Android
frida -p <pid> -l script.js                # attach to running process
frida-trace -U -f com.app -i "open*"       # auto-trace all open* calls
frida-ps -U                                # list processes on USB device
frida-dump <pid> <output.ipa>              # dump decrypted iOS app
```

---

### Windows internals cheat sheet

**PEB (Process Environment Block) — x64 offsets**
| Offset | Field | Notes |
|--------|-------|-------|
| +0x000 | InheritedAddressSpace | BYTE |
| +0x002 | BeingDebugged | BYTE — patch to 0 |
| +0x010 | ImageBaseAddress | base of main EXE |
| +0x018 | Ldr | ptr to PEB_LDR_DATA (module list) |
| +0x020 | ProcessParameters | RTL_USER_PROCESS_PARAMETERS |
| +0x060 | NtGlobalFlag | ULONG — patch to 0 when debugged |
| +0x068 | CriticalSectionTimeout | |
| +0x070 | HeapSegmentReserve | |
| +0x0BC | NtGlobalFlag (32-bit) | 0x70 when debugged |

**TEB (Thread Environment Block) — x64**
| Offset | Field |
|--------|-------|
| GS:0x000 | ptr to TEB itself |
| GS:0x008 | StackBase |
| GS:0x010 | StackLimit |
| GS:0x030 | ptr to PEB |
| GS:0x038 | LastErrorValue |

**EPROCESS offsets (Windows 10/11, varies by build — verify with `dt nt!_EPROCESS`)**
| Field | Win10 21H2 | Win11 22H2 |
|-------|-----------|-----------|
| UniqueProcessId | +0x440 | +0x440 |
| ActiveProcessLinks (Flink) | +0x448 | +0x448 |
| ImageFileName | +0x5A8 | +0x5A8 |
| Token | +0x4B8 | +0x4B8 |
| VadRoot | +0x7D8 | +0x7D8 |

**Always verify offsets at runtime**: `dt nt!_EPROCESS` in WinDbg or `!process 0 0` to find live process

**SSDT (System Service Descriptor Table)**
- `nt!KiServiceTable`: array of `int32` offsets from table base; index = syscall number
- Syscall numbers differ per Windows version — never hardcode; use `NtQuerySystemInformation` or `ntdll` stub to get index
- Common syscalls: `NtOpenProcess`=0x26, `NtAllocateVirtualMemory`=0x18, `NtWriteVirtualMemory`=0x3A (Win10 2004; verify!)
- HVCI: SSDT hooks blocked (kernel pages read-only enforced by hypervisor)

**Key kernel structures for RE**
- `_DRIVER_OBJECT` → `MajorFunction[IRP_MJ_*]` = dispatch table (hook here for driver analysis)
- `_DEVICE_OBJECT` → DeviceExtension = driver-private data
- `_IRP` → `IoStackLocation->Parameters` = IOCTL parameters
- `_LDR_DATA_TABLE_ENTRY`: InLoadOrderLinks, DllBase, EntryPoint, FullDllName — walk for manual module enumeration
- `PsLoadedModuleList`: kernel module list (equiv of PEB Ldr for kernel)

---

### Go / Rust / Swift binary RE

**Go binaries**
- Statically linked by default: binary contains full runtime + all deps — large (5–20MB typical)
- No symbol stripping in default builds: `go tool nm binary` lists all symbols including function names
- Stripped build: `go build -ldflags="-s -w"` removes symbols; IDA/Ghidra still recovers names via `.gopclntab` section
- `.gopclntab`: Go PC-to-line table; contains all function names as strings — survives strip; parse with `GoRE` IDA plugin or `go-re` Ghidra script
- Calling convention (Go 1.17+): register-based (X0–X9 / RAX–R9); older Go: stack-based (all args on stack)
- Goroutine stacks: start small (2KB), grow dynamically; `g` struct at base; `runtime.goexit` as return address sentinel
- String type: `{ptr, len}` pair — not null-terminated; `len` is explicit; in disasm: `mov rax, [str_ptr]; mov rcx, [str_len]`
- Interface type: `{itab_ptr, data_ptr}`; `itab` → `inter` (interface type) + `fun[]` (method table)

**Rust binaries**
- Symbols: mangled as `_ZN<len><crate><len><module><len><fn>E` (Itanium ABI); `rustfilt` or `c++filt` to demangle
- No runtime overhead for most code; panic unwinding via `.eh_frame`/DWARF
- Traits = vtables: `dyn Trait` → fat pointer `{data_ptr, vtable_ptr}`; vtable layout: drop fn, size, align, then methods
- Closures: anonymous structs capturing environment; identify by `{fn_ptr, capture_fields}` pattern
- `Option<T>`: None = 0, Some(x) = 1 with x; `Result<T,E>`: 0 = Ok, 1 = Err
- Bounds checks: compiler inserts `cmp; jae panic_bounds` before every slice index — noise in disasm; recognize and ignore
- `Oxidizer` tool (angr-based): recovers Rust pseudocode from compiled binaries

**Swift binaries**
- Symbols: `$s<module><type><member><signature>` mangling; `swift demangle '$s...'` to decode
- Class layout: ref-counted (strong/weak/unowned); `HeapObject` header = `{isa, refcount}`
- Protocol witness tables (PWT): equiv of vtable for protocols; `{protocol_descriptor, witness_fns[]}`
- `@objc` methods: bridged to ObjC runtime — appear in ObjC method lists, hookable via `objc_msgSend`
- Pure Swift methods: direct calls or through PWT — hook via Frida `Interceptor.attach` on mangled symbol address
- `swift_allocObject` / `swift_release` / `swift_retain`: memory management primitives — xref to find object lifetimes
- Existential container: `{value_buffer[3], metadata_ptr, pwt_ptr}` — 5 words total; value inline if ≤3 words, else heap ptr

### ELF internals (Linux RE)

**Section vs Segment**
- Sections = linker view (`.text`, `.data`, `.bss`, `.rodata`, `.symtab`, `.strtab`, `.rel.text`)
- Segments = loader view (PT_LOAD, PT_DYNAMIC, PT_INTERP); what actually maps into memory
- Stripped binary: no sections, only segments — IDA/Ghidra still works via segments

**GOT/PLT — dynamic linking**
- `.plt`: small stubs; first call → jumps to `_dl_runtime_resolve` → fills `.got.plt` entry
- `.got.plt`: initially points back into `.plt+6`; after first call = real function address
- GOT overwrite: if RELRO not full, overwrite `.got.plt` entry → redirect any libc call
- Full RELRO: `.got.plt` mapped read-only after relocation — GOT overwrite fails
- Find PLT stub for func: `objdump -d -j .plt binary | grep -A3 "func@plt"`

**Key ELF analysis commands**
```bash
readelf -h binary          # ELF header
readelf -S binary          # all sections
readelf -l binary          # program headers (segments)
readelf -d binary          # .dynamic section (DT_NEEDED = deps)
readelf -s binary          # symbol table
readelf -r binary          # relocations
objdump -d -M intel binary # disassemble
nm -D binary               # dynamic symbols
ldd binary                 # shared lib deps
strings -a -n 6 binary     # all strings ≥6 chars
```

**Linux RE tricks**
- `LD_PRELOAD=./hook.so ./target`: inject shared lib, override any libc function
- `strace ./binary`: trace all syscalls; instant understanding of file/network/process behavior
- `ltrace ./binary`: trace library calls
- `/proc/<pid>/maps`: memory layout, regions, permissions, mapped files
- `/proc/<pid>/mem`: read/write any mapped region (requires ptrace permission)
- `ptrace(PTRACE_PEEKDATA/POKEDATA, pid, addr, val)`: debugger primitive; basis for GDB/strace
- Seccomp analysis: `seccomp-tools dump ./binary` — shows allowed syscall whitelist

**Anti-ptrace bypass (Linux)**
- `ptrace(PTRACE_TRACEME, 0, 0, 0)` returns -1 if already traced → process exits; patch to `mov rax, 0`
- `/proc/self/status` check for `TracerPid:` non-zero → patch `strstr`/`fopen` calls
- `SIGSTOP` + `waitpid` self-tracing trick: process traces itself → blocks external debugger

---

### macOS RE specifics

**dyld (dynamic linker)**
- `dyld_shared_cache`: all system frameworks pre-linked into single cache file at `/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/`
- Extract from cache: `dyld-cache-extractor` or `dyldex2`; Ghidra 10.3+ imports directly
- `@rpath`, `@executable_path`, `@loader_path`: relative lib paths; check with `otool -L binary`
- dyld4 (macOS 12+): closure-based; first launch writes closure to `/private/var/db/dyld/`

**Code signing & bypass**
- `codesign -d -vv binary`: show entitlements + team ID
- `codesign --remove-signature binary`: strip signature (breaks on SIP-protected paths)
- `csrutil status`: check SIP (System Integrity Protection)
- Unsigned binary execution: `spctl --add --label "allow" binary` or disable Gatekeeper: `spctl --master-disable`
- Hardened Runtime: prevents `task_for_pid` on the process — blocks debugger attach; bypass: re-sign with `get-task-allow` entitlement

**TCC (Transparency, Consent, Control)**
- Controls access to camera, mic, screen recording, full disk
- DB: `/Library/Application Support/com.apple.TCC/TCC.db` (root) + `~/Library/Application Support/com.apple.TCC/TCC.db`
- RE target: processes that bypass TCC via inherited entitlements or XPC privilege escalation

**XPC services RE**
- Find XPC services: `ls /Applications/App.app/Contents/XPCServices/`
- Protocol RE: hook `NSXPCConnection` or `xpc_connection_send_message`; Frida intercepts both
- Privilege boundary: XPC service often runs as root or with extra entitlements → audit carefully

**macOS useful tools**
```bash
otool -l binary            # load commands (Mach-O headers)
otool -L binary            # linked libraries
nm binary                  # symbols
vmmap <pid>                # memory map (like /proc/pid/maps)
dtrace -n 'syscall::open:entry { trace(copyinstr(arg0)); }'  # syscall trace (needs SIP partial disable)
lldb binary                # debugger
```

---

### Debugger cheat sheets

**WinDbg**
```
bp 0x1400a1234             ; breakpoint at VA
bp kernel32!CreateFileW    ; breakpoint on symbol
bl                         ; list breakpoints
bc *                       ; clear all breakpoints
g                          ; go (continue)
t                          ; trace (step into)
p                          ; step over
k                          ; call stack
r                          ; all registers
r rax                      ; single register
db 0x1400a1234 L10         ; dump 16 bytes
dq rsp L8                  ; dump 8 QWORDs from rsp
u rip L10                  ; unassemble 16 instrs from rip
uf kernel32!CreateFileW    ; unassemble entire function
dd poi(rsp)                ; dereference pointer
!process 0 0               ; list all processes
!process 0 7 notepad.exe   ; detailed process info
dt nt!_EPROCESS <addr>     ; dump EPROCESS struct
!dh <base>                 ; dump PE headers
lm                         ; list modules
x kernel32!*Create*        ; find symbols matching pattern
.reload /f                 ; force symbol reload
!analyze -v                ; analyze crash
vertarget                  ; OS version
.effmach amd64             ; switch to 64-bit context
```

**GDB with pwndbg/PEDA**
```
break *0x401234            # breakpoint at address
break main                 # breakpoint on symbol
info breakpoints           # list
delete 1                   # delete BP #1
run                        # start
continue                   # continue
ni                         # next instruction (step over)
si                         # step into
finish                     # run until return
info registers             # all regs
x/10gx $rsp                # dump 10 qwords from rsp
x/20i $rip                 # disassemble 20 instrs
x/s 0x601050               # print string at addr
set *0x601050 = 0x90909090 # write memory
info proc mappings         # memory map
backtrace                  # call stack
frame 2                    # switch stack frame
disas func_name            # disassemble function
# pwndbg extras:
context                    # full context view
heap                       # heap overview
bins                       # tcache/fastbin/etc
telescope $rsp 20          # dereference chain from rsp
rop --grep "pop rdi"       # find gadgets
```

**x64dbg essentials**
```
F2            ; toggle BP at cursor
F7            ; step into
F8            ; step over
F9            ; run
Ctrl+G        ; goto address/symbol
Ctrl+F        ; search in current module
Ctrl+B        ; search for bytes pattern
Alt+M         ; memory map
Alt+L         ; log window
Right-click → Follow in Dump  ; show in hex dump
Right-click → Set New Origin Here  ; change EIP/RIP
```

---

### ROP (Return-Oriented Programming)

**Concept**: chain `ret`-ending gadgets to build arbitrary computation without injecting code
- Each gadget: `pop rdi; ret` / `mov rax, [rax]; ret` / `syscall; ret` etc.
- Control: overwrite return address on stack → RIP = gadget1 → stack = [gadget1_args, gadget2, gadget2_args, ...]

**Finding gadgets**
```bash
ROPgadget --binary binary --rop          # all gadgets
ROPgadget --binary binary --string "/bin/sh"  # find string
pwntools: rop = ROP(elf); rop.call('system', [next(elf.search(b'/bin/sh'))])
ropper -f binary --search "pop rdi"
```

**Common gadget types**
| Goal | Gadget pattern |
|------|---------------|
| Set RDI (Linux arg1) | `pop rdi; ret` |
| Set RSI (arg2) | `pop rsi; ret` |
| Set RDX (arg3) | `pop rdx; ret` or `pop rdx; pop rbx; ret` |
| Pivot stack | `xchg rax, rsp; ret` / `leave; ret` |
| Syscall | `syscall; ret` |
| Write primitive | `mov [rdi], rsi; ret` |
| Read mem to rax | `mov rax, [rdi]; ret` |

**ret2libc pattern (Linux)**
1. Find `pop rdi; ret` gadget
2. Find `/bin/sh` string in libc
3. Find `system` address in libc
4. Chain: `[pop_rdi_ret][bin_sh_addr][system_addr]`

**ASLR bypass**: leak libc address via format string / partial overwrite / info leak → compute base → compute gadgets

---

### Shellcode analysis & patterns

**Position-independent shellcode**
```asm
; Classic GetEIP (x86)
call next
next: pop eax    ; eax = address of "next" label

; x64: RIP-relative (no call needed)
lea rax, [rip + offset]  ; directly relative
```

**Common shellcode patterns**
- Find kernel32 base: walk PEB→Ldr→InMemoryOrderModuleList (3rd entry = kernel32) → parse PE exports
- API hashing: DJB2 hash of export names, compare to hardcoded hash → resolve address
- Encoded shellcode: XOR loop `xor byte [rsi+rcx], key; loop` — key often single byte or rolling
- Egg hunter: scan memory for 4-byte tag (`\x90\x50\x90\x50`) when payload staged separately
- Staged shellcode: stage1 = connect back + recv → allocate RWX → copy stage2 → jump

**Shellcode analysis workflow**
1. `scdbg` (Linux): emulate shellcode, log API calls without executing
2. `speakeasy` (Mandiant): full Windows shellcode emulation
3. `libemu` / `pylibemu`: x86 shellcode emulator
4. x64dbg: allocate RWX region, copy shellcode bytes, set RIP, single-step

---

### PE format deep dive

**Rich Header** (before MZ header)
- Encrypted with XOR key (last DWORD of Rich header = key)
- Contains: compiler version, linker version, build tool IDs → fingerprints build environment
- Strip = all zeros; malware authors often strip it; presence = legit compiler used
- Parse with `richpe` Python library or `pefile` module

**Overlay**
- Data appended after last section — not mapped into memory
- Common uses: appended zip/archive (self-extracting), certificate, embedded PE
- `pe.get_overlay()` in pefile; `binwalk` finds embedded files automatically

**Certificate Table** (WIN_CERTIFICATE)
- Authenticode signature: `IMAGE_DIRECTORY_ENTRY_SECURITY` → offset+size in PE optional header
- Stripped at runtime — not mapped; verify with `signtool verify /pa binary.exe`
- Stolen signature: malware copies cert table bytes from legit binary → passes casual inspection, fails real verify

**Debug Directory**
- `IMAGE_DIRECTORY_ENTRY_DEBUG` → PDB path in `IMAGE_DEBUG_TYPE_CODEVIEW`
- PDB path leaks: build machine path, internal project name, developer username
- Strip with `strip-debug` or in linker flags; presence = debug info available if PDB found

**Key PE structures for RE**
```
IMAGE_DOS_HEADER.e_lfanew → offset to PE signature
IMAGE_NT_HEADERS:
  Signature = "PE\0\0"
  IMAGE_FILE_HEADER: Machine, NumberOfSections, TimeDateStamp, Characteristics
  IMAGE_OPTIONAL_HEADER:
    ImageBase, SectionAlignment, FileAlignment
    SizeOfImage, SizeOfHeaders
    DataDirectory[16]: exports, imports, resources, exceptions, security, relocs, debug...
IMAGE_SECTION_HEADER: VirtualAddress, VirtualSize, PointerToRawData, SizeOfRawData, Characteristics
```

**VA → file offset**
```python
# for a given VA:
rva = va - imagebase
for section in sections:
    if section.VirtualAddress <= rva < section.VirtualAddress + section.Misc_VirtualSize:
        file_offset = rva - section.VirtualAddress + section.PointerToRawData
```

---

### Memory forensics RE

**Volatility 3 key commands**
```bash
vol -f dump.mem windows.info              # OS version, build
vol -f dump.mem windows.pslist            # process list
vol -f dump.mem windows.pstree           # process tree
vol -f dump.mem windows.cmdline          # command lines
vol -f dump.mem windows.dlllist --pid 1234  # loaded DLLs
vol -f dump.mem windows.malfind          # find injected code (VAD anomalies)
vol -f dump.mem windows.vadinfo --pid 1234  # virtual address descriptors
vol -f dump.mem windows.handles --pid 1234  # open handles
vol -f dump.mem windows.netscan          # network connections
vol -f dump.mem windows.filescan         # file objects in memory
vol -f dump.mem windows.dumpfiles --physaddr 0x...  # dump file from memory
vol -f dump.mem windows.modscan          # kernel modules (finds hidden)
vol -f dump.mem windows.ssdt             # SSDT hooks
vol -f dump.mem windows.callbacks        # kernel callbacks (PsSetCreate*)
```

**Finding injected code**
- `malfind`: finds regions with `PAGE_EXECUTE_READWRITE` + no backing file + PE header = classic injection
- DKOM-hidden process: compare `pslist` (walks EPROCESS list) vs `psscan` (scans pool tags) — extra in psscan = hidden
- Hollowed process: `dlllist` shows ntdll but `vadinfo` shows `PAGE_EXECUTE_READWRITE` where `.text` should be `PAGE_EXECUTE_READ`
- Dump injected region: `vol windows.memmap --dump --pid <pid>` then carve PE with `foremost`

---

### angr practical patterns

```python
import angr, claripy

proj = angr.Project("binary", auto_load_libs=False)

# Find path to address, avoid address
simgr = proj.factory.simgr()
simgr.explore(find=0x401234, avoid=0x401500)
if simgr.found:
    state = simgr.found[0]
    print(state.posix.dumps(0))  # stdin that reached target

# Symbolic input
flag = claripy.BVS("flag", 8*32)  # 32-byte symbolic bitvector
state = proj.factory.full_init_state(stdin=angr.SimFile(name="stdin", content=flag))
simgr = proj.factory.simgr(state)
simgr.explore(find=lambda s: b"correct" in s.posix.dumps(1),
              avoid=lambda s: b"wrong" in s.posix.dumps(1))
solution = simgr.found[0].solver.eval(flag, cast_to=bytes)

# Hook a function
@proj.hook(0x401234, length=5)
def hook(state):
    state.regs.rax = 1  # force return value

# Call a function symbolically
func = proj.factory.callable(0x401234)
result = func(claripy.BVS("arg", 64))
```

### Windows x64 ABI (critical for RE)
- Args: RCX, RDX, R8, R9 (first 4), then stack
- Return: RAX
- Shadow space: 32 bytes caller-reserved on stack before call
- Non-volatile: RBX, RBP, RDI, RSI, R12-R15

### System V ABI (Linux/macOS)
- Args: RDI, RSI, RDX, RCX, R8, R9
- Return: RAX
- No shadow space
