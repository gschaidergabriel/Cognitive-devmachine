FileNotFoundError(2, 'No such file or directory')
Traceback (most recent call last):
  File "/home/andreas/.claude/star/local_bridge_daemon.py", line 209, in execute
    p, meta = operate(s)
              ~~~~~~~^^^
  File "/home/andreas/.claude/star/local_bridge_daemon.py", line 164, in operate
    return op_exec(str(s["command"]), str(s.get("cwd", "")), timeout), {}
           ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/andreas/.claude/star/local_bridge_daemon.py", line 118, in op_exec
    return subprocess.run(["bash", "-lc", cmd], cwd=workdir, capture_output=True,
           ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                           timeout=min(max(timeout, 1), MAX_TIMEOUT))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.14/subprocess.py", line 555, in run
    with Popen(*popenargs, **kwargs) as process:
         ~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.14/subprocess.py", line 1039, in __init__
    self._execute_child(args, executable, preexec_fn, close_fds,
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                        pass_fds, cwd, env,
                        ^^^^^^^^^^^^^^^^^^^
    ...<5 lines>...
                        gid, gids, uid, umask,
                        ^^^^^^^^^^^^^^^^^^^^^^
                        start_new_session, process_group)
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.14/subprocess.py", line 1990, in _execute_child
    raise child_exception_type(errno_num, err_msg, err_filename)
FileNotFoundError: [Errno 2] No such file or directory: '/home/ai-core-node'
