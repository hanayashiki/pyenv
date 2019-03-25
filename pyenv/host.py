from typing import *
import types
import pyenv
import importlib
import socket
import queue
import threading
import sys

class Host:

  def __init__(self, sock : socket.socket, client_addr : Tuple[str, int]):
    self.sock = sock
    self.client_addr = client_addr

    self.stdin_queue = queue.Queue()
    self.out_queue = queue.Queue()

    self.stdin_proxy = pyenv.io.IOProxy(input_queue=self.stdin_queue, output_queue=None)
    self.stdout_proxy = pyenv.io.IOProxy(input_queue=None, output_queue=self.out_queue)
    self.stderr_proxy = pyenv.io.IOProxy(input_queue=None, output_queue=self.out_queue)

    self.stdin_reader = pyenv.io.IOProxyReader(self.stdin_proxy)
    self.stdout_writer = pyenv.io.IOProxyWriter("stdout", self.stdout_proxy)
    self.stderr_writer = pyenv.io.IOProxyWriter("stderr", self.stderr_proxy)

    self.command_handlers = {
      pyenv.protocol.LoadCodeByPath: self.for_load_code_by_path
    }

    self.socket_splitter = pyenv.io.SocketSplitter(protocol=pyenv.protocol.JsonProtocol(),
                                                   sock=self.sock,
                                                   sock_write_source=self.out_queue,
                                                   sock_stdin_dest=self.stdin_queue,
                                                   sock_stdout_dest=None,
                                                   sock_stderr_dest=None)

  def run(self):
    threading.Thread(self.socket_splitter.run).start()

  def for_load_code_by_path(self, m : pyenv.protocol.LoadCodeByPath):
    code = open(m.path, encoding="utf-8")
    code = compile(code, m.path, "exec")

    mod = types.ModuleType(m.path)
    mod.__file__ = m.path
    mod.__package__ = ''

    mod.sys = importlib.import_module("sys")
    mod.os = importlib.import_module("os")

    mod.sys.stdin = self.stdin_reader
    mod.sys.stdout = self.stdout_writer
    mod.sys.stderr = self.stderr_writer

    mod.sys.argv = m.argv
    mod.os.environ = m.environ

    exec(code, mod.__dict__)

def main(argv):
  pass


if __name__ == '__main__':
  main(sys.argv)