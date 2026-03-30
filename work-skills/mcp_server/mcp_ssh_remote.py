# @AI_GENERATED: Kiro v1.0
import os
import sys
import json
import hashlib
import paramiko
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ssh-remote")

SSH_HOST = os.environ.get("SSH_HOST", "")
SSH_PORT = int(os.environ.get("SSH_PORT", "22"))
SSH_USER = os.environ.get("SSH_USER", "")
SSH_PASSWORD = os.environ.get("SSH_PASSWORD", "")
SSH_WORK_DIR = os.environ.get("SSH_WORK_DIR", "")


def _get_ssh_client():
    """Create and return an SSH client connection."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=SSH_HOST,
        port=SSH_PORT,
        username=SSH_USER,
        password=SSH_PASSWORD,
        timeout=15,
    )
    return ssh


def _resolve_work_dir(work_dir: str) -> str:
    """Resolve work_dir: absolute paths used as-is, relative paths joined with SSH_WORK_DIR, empty falls back to SSH_WORK_DIR."""
    if work_dir:
        if work_dir.startswith("/"):
            return work_dir
        elif SSH_WORK_DIR:
            return f"{SSH_WORK_DIR.rstrip('/')}/{work_dir}"
        else:
            return work_dir
    return SSH_WORK_DIR


def _shell_quote(s: str) -> str:
    """Safely quote a string for use as a single shell argument."""
    return "'" + s.replace("'", "'\"'\"'") + "'"


@mcp.tool()
def ssh_exec(command: str, work_dir: str = "", timeout: int = 300) -> str:
    """
    Execute a command on the remote server via SSH.

    Args:
        command: The shell command to execute.
        work_dir: Optional working directory. If provided, will cd to it first.
                  Relative paths are resolved against SSH_WORK_DIR env var.
                  If empty, uses SSH_WORK_DIR as default.
        timeout: Command timeout in seconds (default 300).

    Returns:
        Combined stdout/stderr output and exit code.
    """
    try:
        ssh = _get_ssh_client()
        resolved_dir = _resolve_work_dir(work_dir)
        # Use 'bash -lc' to start a login shell, which sources ~/.bash_profile
        # automatically and sets up the correct environment (e.g. QTDIR for Qt4).
        inner_parts = []
        if resolved_dir:
            inner_parts.append(f"cd {resolved_dir}")
        inner_parts.append(command)
        inner_cmd = " && ".join(inner_parts)
        full_cmd = f"bash -lc {_shell_quote(inner_cmd)}"

        stdin, stdout, stderr = ssh.exec_command(full_cmd, timeout=timeout)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        exit_code = stdout.channel.recv_exit_status()
        ssh.close()

        result = []
        if out.strip():
            result.append(f"=== STDOUT ===\n{out}")
        if err.strip():
            result.append(f"=== STDERR ===\n{err}")
        result.append(f"=== EXIT CODE: {exit_code} ===")
        return "\n".join(result)
    except Exception as e:
        return f"SSH Error: {str(e)}"


@mcp.tool()
def ssh_build(
    work_dir: str,
    clean_cmd: str = "make clean",
    config_cmd: str = "",
    build_cmd: str = "make -j2",
    timeout: int = 600,
) -> str:
    """
    Run a build sequence (clean, configure, build) on the remote server.

    Args:
        work_dir: The directory containing the source code.
        clean_cmd: Clean command (default: make clean).
        config_cmd: Optional configure command (e.g. ./autocfg -g).
        build_cmd: Build command (default: make -j2).
        timeout: Timeout in seconds (default 600).

    Returns:
        Build output and exit code.
    """
    # Build the command sequence:
    # - config_cmd (autocfg) may return non-zero due to non-fatal warnings (e.g. lupdate),
    #   so we use ';' after it to avoid breaking the chain.
    # - clean_cmd && build_cmd are chained with '&&' so build only runs if clean succeeds.
    parts = []
    if config_cmd:
        parts.append(f"rm -f Makefile; {config_cmd}")
    parts.append(f"{clean_cmd} && {build_cmd}")
    full_cmd = " ; ".join(parts)
    return ssh_exec(full_cmd, work_dir=work_dir, timeout=timeout)


@mcp.tool()
def ssh_file_read(file_path: str, tail_lines: int = 0) -> str:
    """
    Read a file from the remote server.

    Args:
        file_path: Absolute path to the file.
        tail_lines: If > 0, only return the last N lines.

    Returns:
        File content.
    """
    if tail_lines > 0:
        cmd = f"tail -n {tail_lines} {file_path}"
    else:
        cmd = f"cat {file_path}"
    return ssh_exec(cmd)


@mcp.tool()
def ssh_list_dir(dir_path: str) -> str:
    """
    List directory contents on the remote server.

    Args:
        dir_path: Absolute path to the directory.

    Returns:
        Directory listing.
    """
    return ssh_exec(f"ls -la {dir_path}")


@mcp.tool()
def ssh_download(remote_path: str, local_dir: str, work_dir: str = "") -> str:
    """
    Download a file from the remote server to a local directory via SFTP.

    Args:
        remote_path: Path to the remote file. Relative paths are resolved against work_dir/SSH_WORK_DIR.
        local_dir: Local directory to save the file into.
        work_dir: Optional working directory for resolving relative remote_path.

    Returns:
        Result message with local file path.
    """
    try:
        resolved_dir = _resolve_work_dir(work_dir)
        if not remote_path.startswith("/"):
            if resolved_dir:
                remote_path = f"{resolved_dir.rstrip('/')}/{remote_path}"

        os.makedirs(local_dir, exist_ok=True)
        filename = remote_path.rsplit("/", 1)[-1]
        local_path = os.path.join(local_dir, filename)

        ssh = _get_ssh_client()
        sftp = ssh.open_sftp()
        sftp.get(remote_path, local_path)
        sftp.close()

        # MD5 verification: compute remote md5 via ssh, compare with local
        _, stdout, _ = ssh.exec_command(f"md5sum {remote_path}")
        remote_md5 = stdout.read().decode().strip().split()[0]
        ssh.close()

        with open(local_path, "rb") as f:
            local_md5 = hashlib.md5(f.read()).hexdigest()

        if remote_md5 == local_md5:
            return f"Downloaded: {remote_path} -> {local_path}\nMD5 OK: {local_md5}"
        else:
            return f"Downloaded: {remote_path} -> {local_path}\nMD5 MISMATCH! remote={remote_md5} local={local_md5}"
    except Exception as e:
        return f"Download Error: {str(e)}"


@mcp.tool()
def ssh_scp_transfer(
    remote_path: str,
    target_host: str,
    target_path: str,
    target_user: str = "",
    target_password: str = "",
    target_port: int = 22,
    work_dir: str = "",
) -> str:
    """
    Transfer a file from the current remote server to another remote machine via SFTP (paramiko).
    The destination file is renamed to "<filename>_<YYYYMMDD>".

    Args:
        remote_path: Source file path on current server. Relative paths resolved against work_dir/SSH_WORK_DIR.
        target_host: Destination machine hostname or IP.
        target_path: Destination directory on the target machine.
        target_user: SSH user for target machine (defaults to current SSH_USER).
        target_password: SSH password for target machine (defaults to current SSH_PASSWORD).
        target_port: SSH port for target machine (default 22).
        work_dir: Optional working directory for resolving relative remote_path.

    Returns:
        Transfer result message.
    """
    from datetime import datetime
    import tempfile

    try:
        resolved_dir = _resolve_work_dir(work_dir)
        if not remote_path.startswith("/"):
            if resolved_dir:
                remote_path = f"{resolved_dir.rstrip('/')}/{remote_path}"

        filename = remote_path.rsplit("/", 1)[-1]
        name, *ext_parts = filename.rsplit(".", 1)
        date_str = datetime.now().strftime("%Y%m%d")
        new_name = f"{name}_{date_str}" + (f".{ext_parts[0]}" if ext_parts else "")

        t_user = target_user or SSH_USER
        t_pass = target_password or SSH_PASSWORD

        # Step 1: Download from source server to local temp file
        src_ssh = _get_ssh_client()
        src_sftp = src_ssh.open_sftp()
        tmp_file = tempfile.mktemp()
        src_sftp.get(remote_path, tmp_file)

        # Get source MD5
        _, stdout, _ = src_ssh.exec_command(f"md5sum {remote_path}")
        src_md5 = stdout.read().decode().strip().split()[0]
        src_sftp.close()
        src_ssh.close()

        # Step 2: Upload to target server
        tgt_ssh = paramiko.SSHClient()
        tgt_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        tgt_ssh.connect(hostname=target_host, port=target_port,
                        username=t_user, password=t_pass, timeout=15)
        tgt_sftp = tgt_ssh.open_sftp()
        dest = f"{target_path.rstrip('/')}/{new_name}"
        tgt_sftp.put(tmp_file, dest)

        # Get target MD5
        _, stdout, _ = tgt_ssh.exec_command(f"md5sum {dest}")
        tgt_md5 = stdout.read().decode().strip().split()[0]
        tgt_sftp.close()
        tgt_ssh.close()

        # Cleanup temp file
        os.remove(tmp_file)

        if src_md5 == tgt_md5:
            return f"Transferred: {remote_path} -> {t_user}@{target_host}:{dest}\nMD5 OK: {src_md5}"
        else:
            return f"Transferred: {remote_path} -> {t_user}@{target_host}:{dest}\nMD5 MISMATCH! source={src_md5} target={tgt_md5}"
    except Exception as e:
        return f"SCP Transfer Error: {str(e)}"


@mcp.tool()
def ssh_upload_dir(
    local_dir: str,
    remote_dir: str,
    target_host: str = "",
    target_user: str = "",
    target_password: str = "",
    target_port: int = 22,
) -> str:
    """
    Recursively upload all files from a local directory to a remote server via SFTP.

    Args:
        local_dir: Local directory path to upload.
        remote_dir: Remote destination directory path.
        target_host: Remote host (defaults to SSH_HOST).
        target_user: SSH user (defaults to SSH_USER).
        target_password: SSH password (defaults to SSH_PASSWORD).
        target_port: SSH port (default 22).

    Returns:
        Upload result with file count.
    """
    try:
        t_host = target_host or SSH_HOST
        t_user = target_user or SSH_USER
        t_pass = target_password or SSH_PASSWORD
        t_port = target_port or SSH_PORT

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=t_host, port=t_port,
                    username=t_user, password=t_pass, timeout=15)
        sftp = ssh.open_sftp()

        def _mkdir_p(remote_path):
            """Recursively create remote directories."""
            dirs_to_create = []
            while True:
                try:
                    sftp.stat(remote_path)
                    break
                except FileNotFoundError:
                    dirs_to_create.append(remote_path)
                    remote_path = remote_path.rsplit("/", 1)[0]
                    if not remote_path:
                        break
            for d in reversed(dirs_to_create):
                sftp.mkdir(d)

        _mkdir_p(remote_dir)

        uploaded = []
        failed = []
        for root, dirs, files in os.walk(local_dir):
            rel_root = os.path.relpath(root, local_dir).replace("\\", "/")
            if rel_root == ".":
                target_dir = remote_dir
            else:
                target_dir = f"{remote_dir.rstrip('/')}/{rel_root}"
                _mkdir_p(target_dir)

            for f in files:
                local_file = os.path.join(root, f)
                remote_file = f"{target_dir.rstrip('/')}/{f}"
                try:
                    sftp.put(local_file, remote_file)
                    uploaded.append(remote_file)
                except Exception as e:
                    failed.append(f"{remote_file}: {e}")

        sftp.close()
        ssh.close()

        result = f"Uploaded {len(uploaded)} files to {t_user}@{t_host}:{remote_dir}"
        if failed:
            result += f"\nFailed {len(failed)} files:\n" + "\n".join(failed)
        return result
    except Exception as e:
        return f"Upload Error: {str(e)}"


@mcp.tool()
def ssh_deploy_file(
    local_file: str,
    remote_dir: str,
    process_name: str = "",
    target_host: str = "",
    target_user: str = "",
    target_password: str = "",
    target_port: int = 22,
) -> str:
    """
    Deploy a local file to a remote server: upload with date suffix, replace the original, verify MD5, and optionally kill the running process.

    Steps:
      1. Upload local file to remote_dir as "<name>_<YYYYMMDD>" (backup copy).
      2. Use mv to replace the original file (same name without date suffix).
      3. Verify MD5 of local file vs remote replaced file.
      4. If process_name is given, check if it's running and kill -9 it.

    Args:
        local_file: Local file path to deploy.
        remote_dir: Remote destination directory.
        process_name: Process name to kill (default: same as filename). Set to "none" to skip.
        target_host: Remote host (defaults to SSH_HOST).
        target_user: SSH user (defaults to SSH_USER).
        target_password: SSH password (defaults to SSH_PASSWORD).
        target_port: SSH port (default 22).

    Returns:
        Deployment result with details of each step.
    """
    from datetime import datetime

    try:
        t_host = target_host or SSH_HOST
        t_user = target_user or SSH_USER
        t_pass = target_password or SSH_PASSWORD
        t_port = target_port or SSH_PORT

        filename = os.path.basename(local_file)
        name, *ext_parts = filename.rsplit(".", 1)
        date_str = datetime.now().strftime("%Y%m%d")
        dated_name = f"{name}_{date_str}" + (f".{ext_parts[0]}" if ext_parts else "")

        remote_dated = f"{remote_dir.rstrip('/')}/{dated_name}"
        remote_target = f"{remote_dir.rstrip('/')}/{filename}"

        # Compute local MD5
        with open(local_file, "rb") as f:
            local_md5 = hashlib.md5(f.read()).hexdigest()

        # Connect to target
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=t_host, port=t_port,
                    username=t_user, password=t_pass, timeout=15)
        sftp = ssh.open_sftp()

        steps = []

        # Step 1: Upload as dated file
        sftp.put(local_file, remote_dated)
        steps.append(f"[1] Uploaded: {remote_dated}")

        # Step 2: mv to replace original
        _, stdout, stderr = ssh.exec_command(f"mv -f {remote_dated} {remote_target}")
        stdout.channel.recv_exit_status()
        steps.append(f"[2] Replaced: {remote_target}")

        # Step 2.5: Add executable permission
        _, stdout, _ = ssh.exec_command(f"chmod +x {remote_target}")
        stdout.channel.recv_exit_status()
        steps.append(f"[2.5] chmod +x: {remote_target}")

        # Step 3: MD5 verify
        _, stdout, _ = ssh.exec_command(f"md5sum {remote_target}")
        remote_md5 = stdout.read().decode().strip().split()[0]
        if local_md5 == remote_md5:
            steps.append(f"[3] MD5 OK: {local_md5}")
        else:
            steps.append(f"[3] MD5 MISMATCH! local={local_md5} remote={remote_md5}")

        # Step 4: Kill process
        proc = process_name if process_name else filename
        if proc.lower() != "none":
            _, stdout, _ = ssh.exec_command(f"ps -ef | grep '{proc}' | grep -v grep")
            ps_output = stdout.read().decode().strip()
            if ps_output:
                _, stdout, _ = ssh.exec_command(
                    f"ps -ef | grep '{proc}' | grep -v grep | awk '{{print $2}}' | xargs kill -9"
                )
                stdout.channel.recv_exit_status()
                steps.append(f"[4] Killed process: {proc}")
            else:
                steps.append(f"[4] Process not found: {proc}")

        sftp.close()
        ssh.close()
        return "\n".join(steps)
    except Exception as e:
        return f"Deploy Error: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
# @AI_GENERATED: end
