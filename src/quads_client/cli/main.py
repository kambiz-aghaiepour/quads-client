import sys
from quads_client.shell import QuadsClientShell


def main():
    """
    Main entry point for quads-client.

    Supports three modes:
    - Interactive mode: quads-client
    - One-shot mode: quads-client <command>
    - Piped mode: echo 'command' | quads-client
    """
    is_oneshot = len(sys.argv) > 1
    is_piped = not sys.stdin.isatty()

    shell = QuadsClientShell(quiet=is_oneshot or is_piped)

    if is_oneshot:
        cmd_str = " ".join(sys.argv[1:])
        exit_code = shell.execute_oneshot_command(cmd_str)
        sys.exit(exit_code)
    elif is_piped:
        exit_code = 0
        for line in sys.stdin:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            result = shell.execute_oneshot_command(line)
            if result != 0:
                exit_code = result
        sys.exit(exit_code)
    else:
        shell.cmdloop()


if __name__ == "__main__":
    main()
