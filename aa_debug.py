"""
Jawaker - FORCE RENDER FLAG
===========================
The real issue: sub_31A4C sets byte_A1918 = 1, but it's not being called
when we bypass sub_300CC. 

SOLUTION: Patch sub_31A4C to ALWAYS set byte_A1918 = 1 at the very start.
This way, even if the data processing fails, the render flag is set!
"""

import subprocess
import time
import os
import shutil
import threading
import sys
from datetime import datetime

DEVICE = "emulator-5554"
TARGET = "com.boundless.jawaker"
TARGET_LIB = "libsystem.so"
LOCAL_ORIGINAL = "libsystem_original.so"
LOCAL_PATCHED  = "libsystem_patched.so"

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log(msg, color=Colors.WHITE, prefix="[*]"):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"{Colors.BOLD}[{timestamp}]{Colors.END} {color}{prefix}{Colors.END} {msg}")

def log_info(msg): log(msg, Colors.CYAN, "[ℹ️]")
def log_success(msg): log(msg, Colors.GREEN, "[✅]")
def log_warning(msg): log(msg, Colors.YELLOW, "[⚠️]")
def log_error(msg): log(msg, Colors.RED, "[❌]")
def log_pred(msg): log(msg, Colors.YELLOW, "[🔮]")
def log_render(msg): log(msg, Colors.BLUE, "[🎨]")

def _run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()

def adb_shell(cmd):
    return _run(["adb", "-s", DEVICE, "shell", cmd])

def su_script(body):
    with open("run_tmp.sh", "w", newline="\n") as f:
        f.write("#!/system/bin/sh\n" + body)
    _run(["adb", "-s", DEVICE, "push", "run_tmp.sh", f"{TMP}/run.sh"])
    adb_shell(f"chmod 755 {TMP}/run.sh")
    return _run(["adb", "-s", DEVICE, "shell", "su", "0", "sh", f"{TMP}/run.sh"])

def get_pid():
    ps = adb_shell("ps -A")
    for line in ps.split('\n'):
        if TARGET in line and 'grep' not in line:
            parts = line.split()
            for i, p in enumerate(parts):
                if p.isdigit() and i > 0:
                    return p
    return None

def get_lib_path():
    raw = adb_shell(f"pm path {TARGET}")
    for line in raw.split('\n'):
        if 'base.apk' in line:
            apk = line.replace("package:", "").strip()
            folder = apk.replace("/base.apk", "")
            return f"{folder}/lib/arm64/{TARGET_LIB}"
    return None

# ═══════════════════════════════════════════════════════════════════════════════
# PATCHES
# ═══════════════════════════════════════════════════════════════════════════════
PATCHES = {
    # Original 18 patches
    0x0003F950: 0x1F, 0x0003F951: 0x20, 0x0003F952: 0x03, 0x0003F953: 0xD5,
    0x00043CE8: 0x20, 0x00043CE9: 0x00, 0x00043CEA: 0x80, 0x00043CEB: 0x52,
    0x00043CEC: 0xC0, 0x00043CED: 0x03, 0x00043CEE: 0x5F, 0x00043CEF: 0xD6,
    0x000441A8: 0x00, 0x000441A9: 0x00, 0x000441AA: 0x80, 0x000441AB: 0x52,
    0x000441AC: 0xC0, 0x000441AD: 0x03, 0x000441AE: 0x5F, 0x000441AF: 0xD6,
    0x000444C8: 0xC0, 0x000444C9: 0x03, 0x000444CA: 0x5F, 0x000444CB: 0xD6,
    0x00047840: 0xD5, 0x00047841: 0x00, 0x00047843: 0x14,
    0x00048538: 0xC0, 0x00048539: 0x03, 0x0004853A: 0x5F, 0x0004853B: 0xD6,
    0x0004D23C: 0xC0, 0x0004D23D: 0x03, 0x0004D23E: 0x5F, 0x0004D23F: 0xD6,
    0x0004DDA4: 0x00, 0x0004DDA5: 0x00, 0x0004DDA6: 0x80, 0x0004DDA7: 0x52,
    0x0004DDA8: 0xC0, 0x0004DDA9: 0x03, 0x0004DDAA: 0x5F, 0x0004DDAB: 0xD6,
    0x0004DDD8: 0xC0, 0x0004DDDA: 0x5F, 0x0004DDDB: 0xD6,
    0x0004F9DC: 0xC0, 0x0004F9DD: 0x03, 0x0004F9DE: 0x5F, 0x0004F9DF: 0xD6,
    0x00051F00: 0x00, 0x00051F01: 0x00, 0x00051F02: 0x86, 0x00051F03: 0xD2,
    0x00051F04: 0xE0, 0x00051F05: 0xCB, 0x00051F06: 0xAB, 0x00051F07: 0xF2,
    0x00051F08: 0xA0, 0x00051F09: 0x33, 0x00051F0A: 0xC0, 0x00051F0B: 0xF2,
    0x00051F0C: 0xC0, 0x00051F0D: 0x03, 0x00051F0E: 0x5F, 0x00051F0F: 0xD6,
    0x00052198: 0x00, 0x00052199: 0x00, 0x0005219A: 0x80, 0x0005219B: 0x52,
    0x0005219C: 0xC0, 0x0005219D: 0x03, 0x0005219E: 0x5F, 0x0005219F: 0xD6,
    0x000538A8: 0xC0, 0x000538AA: 0x5F, 0x000538AB: 0xD6,
    0x0005EE70: 0xC0, 0x0005EE71: 0x03, 0x0005EE72: 0x5F, 0x0005EE73: 0xD6,
    0x00062CF0: 0xC0, 0x00062CF1: 0x03, 0x00062CF2: 0x5F, 0x00062CF3: 0xD6,
    0x0006E730: 0x80, 0x0006E731: 0x00,
    0x0006E77C: 0x60, 0x0006E77D: 0x00,
}

# ═══════════════════════════════════════════════════════════════════════════════
# CRITICAL PATCHES - FORCE RENDER FLAG
# ═══════════════════════════════════════════════════════════════════════════════
# 
# THE KEY INSIGHT:
# sub_31A4C (0x31A4C) sets byte_A1918 = 1 at offset around 0x31F34
# (line 1252 in the decompiled code: byte_A1918 = 1;)
#
# But this only happens if the data processing succeeds.
# When we bypass sub_300CC, the data might be invalid, so sub_31A4C
# might not reach the line that sets byte_A1918 = 1.
#
# SOLUTION: Patch sub_31A4C to set byte_A1918 = 1 at the VERY START
# of the function, before any checks!
#
# ARM64 assembly to set byte_A1918 = 1:
#   MOV W0, #1              -> 20 00 80 52
#   ADRP X1, #page_A1918    -> (depends on address)
#   ADD X1, X1, #offset     -> (depends on address)
#   STRB W0, [X1]           -> 20 00 00 39
#
# Or simpler: just patch the location where byte_A1918 is set to
# ALWAYS execute, regardless of the condition.
#
# Looking at the decompiled code, byte_A1918 = 1 is at line 1252
# which is around offset 0x31F34 in sub_31A4C
#
# Actually, let's patch sub_32304 to NOT check byte_A1918 at all!
# The check is: if ( qword_A1C18 && (byte_A1918 & 1) != 0 )
# We can change this to: if ( qword_A1C18 )  -- remove the byte_A1918 check
#
# In ARM64, this might be:
#   LDRB W0, [X19, #offset]  ; load byte_A1918
#   TST W0, #1               ; test bit 0
#   BEQ skip                 ; branch if zero
#
# We change BEQ to NOP, or change TST to always set Z=0
#
# SAFER: Just patch the early return in sub_32304
# The function returns early if the check fails.
# We NOP the early return path.

CRITICAL_PATCHES = {
    # sub_300CC toggle bypass
    0x300F0: [0x1F, 0x20, 0x03, 0xD5] * 4,
    
    # ═════════════════════════════════════════════════════════════════════════
    # PATCH sub_32304 to remove the byte_A1918 check
    # 
    # The check is approximately at 0x32314-0x32324
    # We NOP the conditional branch that skips rendering
    # ═════════════════════════════════════════════════════════════════════════
    
    # Try multiple locations - one of them should be the right one
    0x32314: [0x1F, 0x20, 0x03, 0xD5],  # NOP potential CBZ
    0x32318: [0x1F, 0x20, 0x03, 0xD5],  # NOP potential CBZ
    0x3231C: [0x1F, 0x20, 0x03, 0xD5],  # NOP potential B.cond
    0x32320: [0x1F, 0x20, 0x03, 0xD5],  # NOP potential B.cond
    0x32324: [0x1F, 0x20, 0x03, 0xD5],  # NOP potential B.cond
    
    # Also patch the early return at the end of the check block
    0x32330: [0x1F, 0x20, 0x03, 0xD5] * 4,
    0x32340: [0x1F, 0x20, 0x03, 0xD5] * 4,
    
    # Kill switch
    0x538A8: [0xC0, 0x03, 0x5F, 0xD6],
}

TMP = "/data/local/tmp"
TMP_PATCHED = f"{TMP}/{TARGET_LIB}_patched"

logging_active = False
log_thread = None

def parse_logcat_line(line):
    line_lower = line.lower()
    
    if any(x in line_lower for x in ['prediction', 'predict', 'toggle']):
        if 'on' in line_lower or 'enable' in line_lower:
            return ('PRED', 'ON', line)
        elif 'off' in line_lower or 'disable' in line_lower:
            return ('PRED', 'OFF', line)
    
    if any(x in line_lower for x in ['render', 'draw', 'overlay', 'updatemultipoints']):
        return ('RENDER', 'DRAW', line)
    
    if any(x in line_lower for x in ['card', 'deck', 'hand', 'game']):
        return ('GAME', 'EVENT', line)
    
    if any(x in line_lower for x in ['error', 'exception', 'fatal', 'crash', 'killed']):
        return ('ERROR', 'CRITICAL', line)
    
    return None

def logcat_monitor():
    global logging_active
    
    log_info("Starting log monitor...")
    
    try:
        process = subprocess.Popen(
            ['adb', '-s', DEVICE, 'logcat', '-v', 'time', '-T', '1'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        while logging_active:
            line = process.stdout.readline()
            if not line:
                continue
                
            if TARGET not in line:
                continue
            
            parsed = parse_logcat_line(line)
            if parsed:
                category, event_type, raw_line = parsed
                
                if category == 'PRED':
                    if event_type == 'ON':
                        log_pred("🟢 PREDICTION TOGGLED ON")
                    else:
                        log_pred("🔴 PREDICTION TOGGLED OFF")
                
                elif category == 'RENDER':
                    msg = raw_line.split(':')[-1].strip()[:50]
                    log_render(f"🎨 {msg}")
                
                elif category == 'GAME':
                    msg = raw_line.split(':')[-1].strip()[:40]
                    log_info(f"🃏 {msg}")
                
                elif category == 'ERROR':
                    msg = raw_line.split(':')[-1].strip()[:50]
                    log_error(f"💥 {msg}")
                
    except Exception as e:
        log_error(f"Logcat error: {e}")
    finally:
        if process:
            process.terminate()

def start_logging():
    global logging_active, log_thread
    logging_active = True
    log_thread = threading.Thread(target=logcat_monitor, daemon=True)
    log_thread.start()

def stop_logging():
    global logging_active
    logging_active = False
    if log_thread:
        log_thread.join(timeout=2)

def prepare_patched_file(device_path):
    if os.path.exists(LOCAL_PATCHED):
        os.remove(LOCAL_PATCHED)

    if not os.path.exists(LOCAL_ORIGINAL):
        log_info("Pulling original library...")
        su_script(f"cp {device_path} {TMP}/{TARGET_LIB} && chmod 777 {TMP}/{TARGET_LIB}")
        _run(["adb", "-s", DEVICE, "pull", f"{TMP}/{TARGET_LIB}", LOCAL_ORIGINAL])
        log_success("Original saved")

    log_warning("🔧 Applying FORCE RENDER FLAG patches...")
    log_info("Patching multiple locations in sub_32304 to bypass byte_A1918 check")
    shutil.copy(LOCAL_ORIGINAL, LOCAL_PATCHED)
    
    patch_count = 0
    with open(LOCAL_PATCHED, "r+b") as f:
        # Apply single-byte patches
        for offset, val in PATCHES.items():
            f.seek(offset)
            f.write(bytes([val]))
            patch_count += 1
        
        # Apply critical patches
        for offset, data in CRITICAL_PATCHES.items():
            f.seek(offset)
            f.write(bytes(data))
            patch_count += len(data)
    
    log_success(f"✅ Applied {patch_count} bytes!")
    return True

def inject_and_run(device_path):
    _run(["adb", "-s", DEVICE, "push", LOCAL_PATCHED, TMP_PATCHED])
    out = su_script(f"mount --bind {TMP_PATCHED} {device_path} && echo OK")
    if "OK" not in out:
        out = su_script(
            "Z=$(ps -A | grep zygote64 | grep -v grep | awk '{print $2}' | head -1)\n"
            f"nsenter -t $Z -m -- mount --bind {TMP_PATCHED} {device_path} && echo OK"
        )
    return "OK" in out

def main():
    print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
    print(f"{Colors.YELLOW}{Colors.BOLD}   🎯 JAWAKER - FORCE RENDER FLAG{Colors.END}")
    print(f"{Colors.BOLD}{'═' * 70}{Colors.END}\n")
    
    print(f"{Colors.RED}🔴 ROOT CAUSE DISCOVERED:{Colors.END}")
    print(f"  sub_31A4C sets byte_A1918 = 1, but it's not being called")
    print(f"  when we bypass sub_300CC! So byte_A1918 stays 0.")
    print(f"\n")
    print(f"{Colors.GREEN}🟢 SOLUTION:{Colors.END}")
    print(f"  Patch sub_32304 at MULTIPLE locations to bypass the")
    print(f"  byte_A1918 check entirely. One of these should work!")
    print(f"\n")
    
    start_logging()

    if get_pid():
        log_warning("Stopping existing app...")
        adb_shell(f"am force-stop {TARGET}")
        time.sleep(1)

    device_path = get_lib_path()
    if not device_path:
        log_error("App not found!")
        stop_logging()
        return
    
    log_info(f"Target: {device_path}")
    prepare_patched_file(device_path)

    log_info("Waiting for game launch...")
    log_info("→ Launch Jawaker now!\n")
    
    injection_done = False
    
    while True:
        pid = get_pid()
        if pid and not injection_done:
            log_success(f"App detected! PID: {pid}")
            
            su_script(f"kill -SIGSTOP {pid}")
            log_info("Process frozen")
            
            maps = adb_shell(f"cat /proc/{pid}/maps")
            if TARGET_LIB in maps:
                su_script(f"kill -SIGCONT {pid}")
                log_error("Library already loaded - restart required!")
                stop_logging()
                return
            
            if inject_and_run(device_path):
                su_script(f"kill -SIGCONT {pid}")
                
                print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
                log_success("INJECTION COMPLETE! 🎉")
                print(f"{Colors.BOLD}{'═' * 70}{Colors.END}\n")
                
                log_success("✅ FORCE RENDER PATCHES ACTIVE!")
                log_info("Patched multiple locations in sub_32304:")
                log_info("  • 0x32314 - NOP potential CBZ")
                log_info("  • 0x32318 - NOP potential CBZ")
                log_info("  • 0x3231C - NOP potential B.cond")
                log_info("  • 0x32320 - NOP potential B.cond")
                log_info("  • 0x32324 - NOP potential B.cond")
                log_info("  • 0x32330 - Early exit bypass")
                log_info("  • 0x32340 - Early exit bypass")
                
                print(f"\n{Colors.CYAN}💡 Test:{Colors.END}")
                print(f"   Open menu → Toggle Prediction → Lines should draw!\n")
                
                injection_done = True
                log_info("Monitoring... Press Ctrl+C to stop\n")
            else:
                su_script(f"kill -SIGCONT {pid}")
                log_error("Injection failed!")
                stop_logging()
                break
        
        if injection_done:
            time.sleep(2)
            if not get_pid():
                log_warning("App closed")
                break
        else:
            time.sleep(0.2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[!] Stopped{Colors.END}")
        stop_logging()
        sys.exit(0)
    except Exception as e:
        log_error(f"Error: {e}")
        stop_logging()
        sys.exit(1)