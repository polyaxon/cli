import threading


_SSH_TUNNEL_CHUNK_SIZE = 32 * 1024
_SSH_TUNNEL_JOIN_TIMEOUT = 1.0


def run_tunnel(client, stdin, stdout, stderr) -> int:
    finished = threading.Event()
    state_lock = threading.Lock()
    close_lock = threading.Lock()
    closed = False
    result_code = 0

    def close_once():
        nonlocal closed
        with close_lock:
            if closed:
                return
            closed = True
        try:
            client.close()
        except Exception:
            pass

    def finish_clean():
        with state_lock:
            if finished.is_set():
                return
            finished.set()
        close_once()

    def fail(message):
        nonlocal result_code
        with state_lock:
            if finished.is_set():
                return
            result_code = 1
            finished.set()
        close_once()
        stderr.write("{}\n".format(message))
        stderr.flush()

    def stdin_to_ws():
        read = getattr(stdin, "read1", None) or stdin.read
        while not finished.is_set():
            try:
                data = read(_SSH_TUNNEL_CHUNK_SIZE)
            except OSError:
                finish_clean()
                return
            except Exception as e:
                fail("polyaxon ssh tunnel: stdin read failed: {}".format(e))
                return
            if not data:
                finish_clean()
                return
            if finished.is_set():
                return
            try:
                client.send(data)
            except Exception as e:
                fail("polyaxon ssh tunnel: stdin send failed: {}".format(e))
                return

    def ws_to_stdout():
        while not finished.is_set():
            try:
                data = client.recv()
            except Exception as e:
                fail("polyaxon ssh tunnel: websocket recv failed: {}".format(e))
                return
            if not data:
                finish_clean()
                return
            if finished.is_set():
                return
            try:
                stdout.write(data)
                stdout.flush()
            except Exception as e:
                fail("polyaxon ssh tunnel: stdout write failed: {}".format(e))
                return

    stdin_thread = threading.Thread(target=stdin_to_ws, daemon=True)
    ws_thread = threading.Thread(target=ws_to_stdout, daemon=True)
    stdin_thread.start()
    ws_thread.start()

    finished.wait()
    close_once()
    ws_thread.join(timeout=_SSH_TUNNEL_JOIN_TIMEOUT)
    return result_code
